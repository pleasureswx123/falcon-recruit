"""履历核验：Gap 计算 & 稳定性分析 (TDD §3.2)。

规则：
- Gap = 下一段工作开始 - 上一段结束；超过 3 个月 (>90 天 / 近似 >3 月) 记录。
- 若此窗口落在教育经历时段内（即"在校期间"），标记为教育衔接，不计入风险。
- 平均在职时长 = sum(month of each experience) / count。
- 平均 < 12 个月视为"频繁跳槽"。
"""
from __future__ import annotations

from datetime import date

from app.schemas.profile import (
    CareerGap,
    ResumeProfile,
    VerificationReport,
)

_GAP_THRESHOLD_MONTHS = 3  # PRD: >90 天 ≈ >3 个月


def _to_date(ym: str | None, *, end: bool = False) -> date | None:
    if not ym:
        return None
    try:
        y, m = [int(x) for x in ym.split("-")]
    except ValueError:
        return None
    return date(y, m, 28 if end else 1)


def _months_diff(later: date, earlier: date) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


def _covers(educations, from_d: date, to_d: date) -> bool:
    """判断 [from_d, to_d] 是否被任一教育时段覆盖。"""
    for ed in educations:
        ed_start = _to_date(ed.start)
        ed_end = _to_date(ed.end, end=True) or date.today()
        if not ed_start:
            continue
        if ed_start <= from_d and to_d <= ed_end:
            return True
    return False


def verify_profile(profile: ResumeProfile) -> VerificationReport:
    report = VerificationReport()
    if not profile.experiences:
        return report

    # 按开始时间排序；缺失开始时间的排到最后
    experiences = sorted(
        [e for e in profile.experiences if e.start],
        key=lambda e: e.start or "9999-99",
    )

    # --- Gap 计算 ---
    for prev, nxt in zip(experiences, experiences[1:]):
        prev_end = _to_date(prev.end, end=True) or date.today()
        next_start = _to_date(nxt.start)
        if not next_start:
            continue
        months = _months_diff(next_start, prev_end)
        if months > _GAP_THRESHOLD_MONTHS:
            covered = _covers(profile.educations, prev_end, next_start)
            report.gaps.append(
                CareerGap(
                    from_end=prev.end,
                    to_start=nxt.start,
                    months=months,
                    is_covered_by_education=covered,
                    note=(
                        f"{prev.company or '上一段'} 结束至 "
                        f"{nxt.company or '下一段'} 入职相隔 {months} 个月"
                        + ("（在读期间）" if covered else "")
                    ),
                )
            )

    real_gaps = [g for g in report.gaps if not g.is_covered_by_education]
    if real_gaps:
        total = sum(g.months for g in real_gaps)
        report.risk_flags.append(
            f"履历断层：{len(real_gaps)} 段空窗，合计 {total} 个月"
        )

    # --- 平均在职时长 ---
    def _tenure(e):
        s = _to_date(e.start)
        en = _to_date(e.end, end=True) or date.today()
        if not s:
            return 0
        return _months_diff(en, s)

    tenures = [_tenure(e) for e in experiences]
    tenures = [t for t in tenures if t > 0]
    if tenures:
        report.average_tenure_months = round(sum(tenures) / len(tenures), 1)
        if report.average_tenure_months < 12:
            report.job_hopper = True
            report.risk_flags.append(
                f"频繁跳槽：平均在职 {report.average_tenure_months:.1f} 个月"
            )

    return report
