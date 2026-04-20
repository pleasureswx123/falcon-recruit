"""OpenAI 兼容的 LLM 客户端 (Phase 6)。

支持 OpenAI / DeepSeek / Moonshot / 硅基流动 等任何兼容 /v1/chat/completions 的厂商。
无 key 时 `is_enabled()` 返回 False，`chat_json()` 返回 None。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def is_enabled() -> bool:
    s = get_settings()
    return bool(s.openai_api_key)


def _base_url() -> str:
    url = get_settings().openai_base_url or "https://api.openai.com/v1"
    return url.rstrip("/")


def _extract_json(text: str) -> dict | list | None:
    """宽容解析模型输出：去掉 ```json 围栏 + 截取最外层 JSON。"""
    s = text.strip()
    s = _CODE_FENCE.sub("", s).strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # 兜底：取首个 { 或 [ 到最后一个匹配的 } 或 ]
    first_obj = s.find("{")
    first_arr = s.find("[")
    starts = [x for x in (first_obj, first_arr) if x >= 0]
    if not starts:
        return None
    start = min(starts)
    end_obj = s.rfind("}")
    end_arr = s.rfind("]")
    end = max(end_obj, end_arr)
    if end <= start:
        return None
    try:
        return json.loads(s[start : end + 1])
    except json.JSONDecodeError:
        logger.warning("LLM JSON 解析失败，已降级到 None: %s", s[:200])
        return None


async def chat_json(
    *,
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    timeout: float = 60.0,
) -> dict | list | None:
    """调用 LLM 并解析为 JSON。失败或未配置 key 时返回 None。"""
    s = get_settings()
    if not s.openai_api_key:
        return None

    payload: dict[str, Any] = {
        "model": s.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {s.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{_base_url()}/chat/completions",
                headers=headers,
                json=payload,
            )
    except httpx.HTTPError as exc:
        logger.warning("LLM 请求网络异常: %s", exc)
        return None

    if resp.status_code == 400:
        # 部分厂商（DeepSeek）不支持 response_format，重试一次不带该字段
        try:
            payload.pop("response_format", None)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{_base_url()}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            logger.warning("LLM 重试失败: %s", exc)
            return None

    if resp.status_code != 200:
        logger.warning("LLM %d: %s", resp.status_code, resp.text[:300])
        return None

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        logger.warning("LLM 响应格式异常: %s", exc)
        return None

    return _extract_json(content)
