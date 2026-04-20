"use client"

import { AlertTriangle, Briefcase, GraduationCap } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type {
  CareerGap,
  EducationExperience,
  WorkExperience,
} from "@/lib/api/reports"
import { DEGREE_LABEL } from "@/lib/api/reports"

interface Props {
  experiences: WorkExperience[]
  educations: EducationExperience[]
  gaps: CareerGap[]
}

type TimelineItem =
  | { kind: "work"; start: string; end: string | null; data: WorkExperience }
  | {
      kind: "edu"
      start: string
      end: string | null
      data: EducationExperience
    }
  | { kind: "gap"; start: string; end: string; data: CareerGap }

function asDateStr(s: string | null | undefined): string {
  return s ?? ""
}

function toComparable(s: string): number {
  // 将 "YYYY-MM" / "YYYY.MM" / "至今" 等都转成 YYYYMM，空串排最后。
  if (!s) return 209912
  const m = s.match(/(\d{4})[.\-/](\d{1,2})/)
  if (m) return parseInt(m[1]) * 100 + parseInt(m[2])
  return parseInt(s.replace(/\D/g, "").slice(0, 6) || "209912")
}

function formatRange(start: string | null, end: string | null): string {
  const s = start || "—"
  const e = end || "至今"
  return `${s} — ${e}`
}

export function ExperienceTimeline({ experiences, educations, gaps }: Props) {
  const realGaps = gaps.filter((g) => !g.is_covered_by_education)

  const items: TimelineItem[] = [
    ...experiences.map<TimelineItem>((e) => ({
      kind: "work",
      start: asDateStr(e.start),
      end: e.end,
      data: e,
    })),
    ...educations.map<TimelineItem>((e) => ({
      kind: "edu",
      start: asDateStr(e.start),
      end: e.end,
      data: e,
    })),
    ...realGaps.map<TimelineItem>((g) => ({
      kind: "gap",
      start: asDateStr(g.from_end),
      end: asDateStr(g.to_start),
      data: g,
    })),
  ]

  items.sort((a, b) => toComparable(b.start) - toComparable(a.start))

  if (items.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">履历时间轴</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          暂无可用的工作或教育经历
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">履历时间轴</CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="relative flex flex-col gap-4 border-l border-muted pl-6">
          {items.map((it, idx) => (
            <TimelineNode key={idx} item={it} />
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}

function TimelineNode({ item }: { item: TimelineItem }) {
  if (item.kind === "work") {
    const w = item.data
    return (
      <li className="relative">
        <span className="absolute -left-[30px] top-1 flex h-5 w-5 items-center justify-center rounded-full border-2 border-indigo-500 bg-background">
          <Briefcase className="h-2.5 w-2.5 text-indigo-500" />
        </span>
        <div className="flex flex-col gap-0.5">
          <div className="text-xs text-muted-foreground">
            {formatRange(w.start, w.end)}
          </div>
          <div className="text-sm font-medium">
            {w.company ?? "—"}
            {w.title ? ` · ${w.title}` : ""}
          </div>
          {w.description && (
            <div className="text-xs text-muted-foreground">{w.description}</div>
          )}
        </div>
      </li>
    )
  }
  if (item.kind === "edu") {
    const e = item.data
    return (
      <li className="relative">
        <span className="absolute -left-[30px] top-1 flex h-5 w-5 items-center justify-center rounded-full border-2 border-sky-500 bg-background">
          <GraduationCap className="h-2.5 w-2.5 text-sky-500" />
        </span>
        <div className="flex flex-col gap-0.5">
          <div className="text-xs text-muted-foreground">
            {formatRange(e.start, e.end)}
          </div>
          <div className="text-sm font-medium">
            {e.school ?? "—"}
            {e.major ? ` · ${e.major}` : ""}
            <span className="ml-2 rounded bg-sky-50 px-1.5 py-0.5 text-[10px] text-sky-700">
              {DEGREE_LABEL[e.degree]}
            </span>
          </div>
        </div>
      </li>
    )
  }
  // gap
  const g = item.data
  return (
    <li className="relative">
      <span className="absolute -left-[30px] top-1 flex h-5 w-5 items-center justify-center rounded-full border-2 border-rose-400 bg-rose-50">
        <AlertTriangle className="h-2.5 w-2.5 text-rose-500" />
      </span>
      <div className="flex flex-col gap-0.5 rounded-md border border-rose-200 bg-rose-50/60 px-3 py-2">
        <div className="text-xs text-rose-700">
          {g.from_end ?? "—"} — {g.to_start ?? "—"} · 空窗 {g.months} 个月
        </div>
        <div className="text-xs text-rose-700/80">
          {g.note ?? "履历断层：建议在面试中询问这段时间的经历与原因"}
        </div>
      </div>
    </li>
  )
}
