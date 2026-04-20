"""应用全局配置。

通过 pydantic-settings 自动加载 .env 文件与环境变量。
"""
from functools import lru_cache
from typing import Annotated, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """猎鹰 Falcon AI 后端配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础
    app_name: str = Field(default="Falcon AI")
    app_env: str = Field(default="development")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=True)

    # 服务监听
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

    # CORS（禁用 JSON 解析，由下方 validator 自行按逗号切分）
    cors_origins: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    # 数据库（Phase 2）
    database_url: str = Field(default="sqlite+aiosqlite:///./falcon.db")
    database_echo: bool = Field(default=False)

    # Redis（Phase 3 启用）
    redis_url: str | None = Field(default=None)

    # 存储路径（Phase 3：ZIP 解压与重命名产物）
    storage_root: str = Field(default="./storage")
    max_upload_mb: int = Field(default=200)

    # LLM（Phase 4 启用）
    openai_api_key: str | None = Field(default=None)
    openai_base_url: str | None = Field(default=None)
    llm_model: str = Field(default="gpt-4o")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例配置获取，避免重复读取 .env。"""
    return Settings()
