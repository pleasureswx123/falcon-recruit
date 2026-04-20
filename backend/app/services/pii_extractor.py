"""PII 提取器 (TDD §3.1 · 特征提取)。

从简历文本中提取：
- 手机号（中国大陆 11 位）
- 邮箱
- 微信号（wechat/wx/微信 标签后跟 4-30 位 ASCII）
- 姓名（启发式：标签命中 > 文档开头常见姓氏匹配）
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# 手机号：13/14/15/16/17/18/19 开头的 11 位数字，边界用非数字分隔
_PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")

# 邮箱（RFC 简化版）
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
)

# 微信号：标签 + 4-30 ASCII，允许字母/数字/下划线/连字符
_WECHAT_RE = re.compile(
    r"(?:微信号?|wechat|wx)\s*[:：]?\s*([A-Za-z][A-Za-z0-9_\-]{3,29})",
    re.IGNORECASE,
)

# 姓名标签命中模式
_NAME_LABEL_RE = re.compile(
    r"(?:姓\s*名|名\s*字|Name)\s*[:：]?\s*([\u4e00-\u9fa5]{2,4}|[A-Z][a-zA-Z]+\s?[A-Z][a-zA-Z]+)"
)

# 常见中文姓氏（覆盖约 95% 人口，启发式降级用）
_COMMON_SURNAMES = set(
    "王李张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧"
    "程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜"
    "范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段章钱汤"
    "尹黎易常武乔贺赖龚文欧阳司马上官诸葛"
)


@dataclass(slots=True, frozen=True)
class PII:
    """单文档提取到的 PII 特征集合。"""

    phones: tuple[str, ...] = ()
    emails: tuple[str, ...] = ()
    wechats: tuple[str, ...] = ()
    names: tuple[str, ...] = ()

    @property
    def primary_phone(self) -> str | None:
        return self.phones[0] if self.phones else None

    @property
    def primary_email(self) -> str | None:
        return self.emails[0] if self.emails else None

    @property
    def primary_wechat(self) -> str | None:
        return self.wechats[0] if self.wechats else None

    @property
    def primary_name(self) -> str | None:
        return self.names[0] if self.names else None

    def is_empty(self) -> bool:
        return not (self.phones or self.emails or self.wechats)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def _guess_names_from_header(text: str) -> list[str]:
    """启发式：文档前 20 行里找 2-4 字中文人名（首字为常见姓氏）。"""
    found: list[str] = []
    for line in text.splitlines()[:20]:
        stripped = line.strip()
        if not stripped or len(stripped) > 20:
            continue
        # 仅保留中文字符扫描
        for m in re.finditer(r"[\u4e00-\u9fa5]{2,4}", stripped):
            token = m.group()
            # 复姓优先
            if len(token) >= 3 and token[:2] in _COMMON_SURNAMES:
                found.append(token)
                continue
            if token[0] in _COMMON_SURNAMES:
                found.append(token)
    return found


def extract_pii(text: str) -> PII:
    """从纯文本中提取 PII。"""
    if not text:
        return PII()

    phones = _dedupe_preserve_order(_PHONE_RE.findall(text))
    emails = _dedupe_preserve_order(
        m.group(0).lower() for m in _EMAIL_RE.finditer(text)
    )
    wechats_raw = [m.group(1) for m in _WECHAT_RE.finditer(text)]
    # 排除误命中：纯数字（通常是手机号重复命中）
    wechats = _dedupe_preserve_order(
        [w for w in wechats_raw if not w.isdigit()]
    )

    names: list[str] = []
    for m in _NAME_LABEL_RE.finditer(text):
        candidate = m.group(1).strip()
        if candidate:
            names.append(candidate)
    # 启发式兜底
    if not names:
        names = _guess_names_from_header(text)
    names = _dedupe_preserve_order(names)

    return PII(
        phones=tuple(phones),
        emails=tuple(emails),
        wechats=tuple(wechats),
        names=tuple(names),
    )
