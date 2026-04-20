"""结构化日志配置。

约定：
- 开发环境：带颜色的人类可读格式（默认 uvicorn 行为）。
- 生产环境：单行 key=value 结构化日志，便于日志聚合（Loki/ES）解析。

调用入口：main.py 在 create_app 前调用 configure_logging()。
"""
from __future__ import annotations

import logging
import sys
from typing import Any

from app.core.config import get_settings


class _KeyValueFormatter(logging.Formatter):
    """key=value 结构化输出，适合生产日志采集。"""

    _STD_KEYS = {
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info",
        "lineno", "funcName", "created", "msecs", "relativeCreated",
        "thread", "threadName", "processName", "process", "message",
        "asctime", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        ts = self.formatTime(record, "%Y-%m-%dT%H:%M:%S")
        base = (
            f'ts={ts} level={record.levelname} logger={record.name} '
            f'msg={self._quote(record.getMessage())}'
        )
        # 附加 LogRecord.extra 字段
        extras: list[str] = []
        for k, v in record.__dict__.items():
            if k in self._STD_KEYS or k.startswith("_"):
                continue
            extras.append(f"{k}={self._quote(v)}")
        if extras:
            base = base + " " + " ".join(extras)
        if record.exc_info:
            base = base + " exc=" + self._quote(self.formatException(record.exc_info))
        return base

    @staticmethod
    def _quote(val: Any) -> str:
        s = str(val).replace("\n", " ").replace("\r", " ")
        if any(c in s for c in (" ", "=", '"')):
            s = '"' + s.replace('"', '\\"') + '"'
        return s


def configure_logging() -> None:
    """根据 APP_ENV / DEBUG 选择日志格式与级别。"""
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO

    root = logging.getLogger()
    # 清理 uvicorn 默认 handler 避免重复输出
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stdout)
    if settings.app_env == "production":
        handler.setFormatter(_KeyValueFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    root.addHandler(handler)
    root.setLevel(level)

    # 压低 SQLAlchemy 引擎/访问日志噪声（开启 DATABASE_ECHO 时手动打开）
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
