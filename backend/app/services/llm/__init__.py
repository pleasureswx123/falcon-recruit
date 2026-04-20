"""LLM 能力封装 (Phase 6)。

无 key 时所有调用返回 None，由上层业务走规则式降级。
"""
from app.services.llm.client import chat_json, is_enabled

__all__ = ["chat_json", "is_enabled"]
