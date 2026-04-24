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

    # 数据库（Phase 2）
    database_url: str = Field(
        default="postgresql+asyncpg://falcon:falcon_dev_pw@127.0.0.1:5432/falcon"
    )
    database_echo: bool = Field(default=False)

    # Redis（Phase 3 启用，Phase 6 用于 Session 存储）
    # 开发环境：redis://127.0.0.1:6379/0（宿主机映射端口）
    # 生产环境：redis://redis:6379/0（Docker 容器网络）
    redis_url: str | None = Field(default=None)

    # 存储路径（Phase 3：ZIP 解压与重命名产物）
    storage_root: str = Field(default="./storage")
    max_upload_mb: int = Field(default=200)

    # LLM（Phase 4 启用）
    openai_api_key: str | None = Field(default=None)
    openai_base_url: str | None = Field(default=None)
    llm_model: str = Field(default="gpt-4o")

    # 限流（per-IP，单位/分钟）
    rate_limit_upload: str = Field(default="10/minute")
    rate_limit_export: str = Field(default="30/minute")
    # ZIP 炸弹防御：解压后总大小上限倍数（相对于 max_upload_mb）与文件数上限
    zip_expand_ratio_max: int = Field(default=10)
    zip_max_files: int = Field(default=5000)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例配置获取，避免重复读取 .env。"""
    return Settings()
