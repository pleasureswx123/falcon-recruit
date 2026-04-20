"""PII-Linker 分拣引擎 (TDD §3.1 · 关联逻辑)。

输入：一批 `ParsedDoc`（每份代表 ZIP 内一个已解析文件）。
输出：合并后的若干 `CandidateGroup`，每个 group 绑定同一个候选人。

核心策略：
1. 用 Union-Find 基于"任意一个 PII 键相同 → 合并"构建连通分量；
2. 对未提取到 PII 的文档走补偿分支：按 `zip_member` 的同级目录聚类，
   若一个目录下只有一个已识别候选人组，则把该目录下的孤立文件也挂进去。
"""
from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from app.models.file import FileType
from app.services.pii_extractor import PII

_FILENAME_SIMILARITY_THRESHOLD = 0.55
_NAME_CANDIDATE_RE = re.compile(r"[\u4e00-\u9fa5]{2,4}")


@dataclass(slots=True)
class ParsedDoc:
    """PII-Linker 的输入行。"""

    file_id: str
    zip_member: str           # ZIP 内路径，用于目录聚类
    file_type: FileType       # RESUME / PORTFOLIO / UNKNOWN（由 zip_processor 推断）
    pii: PII
    text_len: int = 0         # 用于挑选"主简历"（越大越像简历）


@dataclass(slots=True)
class CandidateGroup:
    """合并后的一个候选人分组。"""

    name: str | None = None
    phone: str | None = None
    email: str | None = None
    wechat: str | None = None
    file_ids: list[str] = field(default_factory=list)
    reason: str = ""          # 关联理由（诊断用）


# ---------- Union-Find ----------

class _UF:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        while self.parent.get(x, x) != x:
            self.parent[x] = self.parent.get(self.parent.get(x, x), x)
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def ensure(self, x: str) -> None:
        self.parent.setdefault(x, x)


def _pii_keys(doc: ParsedDoc) -> list[str]:
    """把一份文档的所有 PII 键扁平化为字符串列表，用于 UF 合并。"""
    keys: list[str] = []
    for p in doc.pii.phones:
        keys.append(f"phone:{p}")
    for e in doc.pii.emails:
        keys.append(f"email:{e}")
    for w in doc.pii.wechats:
        keys.append(f"wechat:{w}")
    return keys


def _parent_dir(member: str) -> str:
    return os.path.dirname(member.replace("\\", "/")).rstrip("/")


def link(docs: list[ParsedDoc]) -> list[CandidateGroup]:
    """核心关联算法。"""
    if not docs:
        return []

    uf = _UF()
    # 每个文档至少成为一个独立节点
    for doc in docs:
        uf.ensure(f"doc:{doc.file_id}")

    # PII 键 <-> 文档节点 连边
    for doc in docs:
        doc_key = f"doc:{doc.file_id}"
        for k in _pii_keys(doc):
            uf.ensure(k)
            uf.union(doc_key, k)

    # 收集：以"文档连通分量根"为 key
    buckets: dict[str, list[ParsedDoc]] = defaultdict(list)
    for doc in docs:
        root = uf.find(f"doc:{doc.file_id}")
        buckets[root].append(doc)

    groups = [_build_group(docs_in_bucket) for docs_in_bucket in buckets.values()]

    # 补偿 1：同级目录聚类。无 PII 的 group 尝试并入目录内唯一的有效 group。
    _absorb_by_directory(groups, docs)
    # 补偿 2：文件名相似度聚类。对剩余孤立 group 按文件名/候选人姓名相似度合并。
    _absorb_by_filename_similarity(groups, docs)
    # 去掉被吸收后变空的 group
    return [g for g in groups if g.file_ids]


def _build_group(docs: list[ParsedDoc]) -> CandidateGroup:
    """从连通分量里选出代表性 PII。"""
    phones = {p for d in docs for p in d.pii.phones}
    emails = {e for d in docs for e in d.pii.emails}
    wechats = {w for d in docs for w in d.pii.wechats}
    # 名字：优先出现在"文本最长且为简历"的文档里
    docs_sorted = sorted(
        docs,
        key=lambda d: (d.file_type == FileType.RESUME, d.text_len),
        reverse=True,
    )
    name = next(
        (d.pii.primary_name for d in docs_sorted if d.pii.primary_name),
        None,
    )
    reasons: list[str] = []
    if phones:
        reasons.append(f"手机号={sorted(phones)[0]}")
    if emails:
        reasons.append(f"邮箱={sorted(emails)[0]}")
    if wechats:
        reasons.append(f"微信={sorted(wechats)[0]}")

    return CandidateGroup(
        name=name,
        phone=next(iter(sorted(phones)), None),
        email=next(iter(sorted(emails)), None),
        wechat=next(iter(sorted(wechats)), None),
        file_ids=[d.file_id for d in docs_sorted],
        reason=" / ".join(reasons) if reasons else "仅目录聚类",
    )


def _absorb_by_directory(groups: list[CandidateGroup], docs: list[ParsedDoc]) -> None:
    doc_map = {d.file_id: d for d in docs}
    # 目录 -> 含 PII 的 group 列表
    dir_to_groups: dict[str, set[int]] = defaultdict(set)
    for idx, g in enumerate(groups):
        if g.phone or g.email or g.wechat:
            for fid in g.file_ids:
                dir_to_groups[_parent_dir(doc_map[fid].zip_member)].add(idx)

    for g in groups:
        if g.phone or g.email or g.wechat:
            continue
        # 本 group 全是孤立无 PII 文件
        target_indices: set[int] = set()
        for fid in g.file_ids:
            candidates = dir_to_groups.get(_parent_dir(doc_map[fid].zip_member), set())
            target_indices |= candidates
        if len(target_indices) == 1:
            target = groups[next(iter(target_indices))]
            target.file_ids.extend(g.file_ids)
            target.reason += "；同目录孤立文件聚类吸收"
            g.file_ids.clear()


def _filename_stem(member: str) -> str:
    """去扩展名、去目录、去常见噪声前缀，留作候选 token。"""
    base = os.path.basename(member.replace("\\", "/"))
    stem = os.path.splitext(base)[0]
    # 剥离 BOSS 直聘等常见平台前后缀
    for noise in ("BOSS直聘-", "简历-", "-简历", "作品集-", "-作品集"):
        stem = stem.replace(noise, "")
    return stem.strip()


def _name_tokens(stem: str) -> list[str]:
    """从文件名里抽取中文姓名候选（2~4 连续汉字）。"""
    return _NAME_CANDIDATE_RE.findall(stem)


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _absorb_by_filename_similarity(
    groups: list[CandidateGroup], docs: list[ParsedDoc]
) -> None:
    """对剩余孤立 group，按文件名 stem / 姓名 token 相似度并入已识别 group。

    策略：
    - 仅对仍孤立（无 PII）的 group 生效；
    - 目标 group 必须含 PII 且已知姓名；
    - 命中条件任一成立即合并：
        a) 姓名完全出现在孤立文件名中；
        b) 文件名 stem 与另一已匹配文件的 stem SequenceMatcher ≥ 阈值。
    """
    doc_map = {d.file_id: d for d in docs}

    # 已识别的 group：预计算姓名 + 所有成员文件名 stems
    identified: list[tuple[int, CandidateGroup, list[str]]] = []
    for idx, g in enumerate(groups):
        if not (g.phone or g.email or g.wechat):
            continue
        stems = [
            _filename_stem(doc_map[fid].zip_member)
            for fid in g.file_ids
            if fid in doc_map
        ]
        identified.append((idx, g, stems))

    if not identified:
        return

    for g in groups:
        if g.phone or g.email or g.wechat:
            continue
        # 评估每份孤立文件：找最相似的已识别 group
        best_idx: int | None = None
        best_score = 0.0
        for fid in g.file_ids:
            doc = doc_map.get(fid)
            if doc is None:
                continue
            stem = _filename_stem(doc.zip_member)
            if not stem:
                continue
            tokens = _name_tokens(stem)
            for idx, target, target_stems in identified:
                # a) 目标 group 的姓名直接出现在文件名里
                if target.name and target.name in stem:
                    score = 1.0
                # b) 目标 group 已有文件名 stem 与当前 stem 相似
                else:
                    score = max(
                        (_similarity(stem, ts) for ts in target_stems),
                        default=0.0,
                    )
                    # 叠加：若任一 token 命中目标 group 姓名，加权提升
                    if target.name and tokens and target.name in tokens:
                        score = max(score, 0.9)
                if score > best_score:
                    best_score = score
                    best_idx = idx

        if best_idx is not None and best_score >= _FILENAME_SIMILARITY_THRESHOLD:
            target = groups[best_idx]
            target.file_ids.extend(g.file_ids)
            target.reason += f"；文件名相似度聚类吸收(score={best_score:.2f})"
            g.file_ids.clear()
