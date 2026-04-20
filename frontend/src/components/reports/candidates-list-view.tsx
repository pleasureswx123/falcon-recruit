"use client"

import * as React from "react"
import Link from "next/link"
import { ArrowUpDown, CheckCircle2, Search, Users } from "lucide-react"

import { ExportMenu } from "@/components/exports/export-menu"
import { ScoreBadge } from "@/components/reports/score-badge"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { Candidate } from "@/lib/api/candidates"
import { useCandidates } from "@/lib/hooks/use-candidates"
import { useJobs } from "@/lib/hooks/use-jobs"

type SortField = "score" | "updated_at" | "name"
type SortDir = "asc" | "desc"

const ALL_JOB = "__all__"

export function CandidatesListView() {
  const [jobId, setJobId] = React.useState<string | undefined>(undefined)
  const [keyword, setKeyword] = React.useState("")
  const [sortField, setSortField] = React.useState<SortField>("score")
  const [sortDir, setSortDir] = React.useState<SortDir>("desc")

  const { data: jobsData } = useJobs({ page: 1, page_size: 100 })
  const { data, isLoading } = useCandidates({
    job_id: jobId,
    keyword: keyword.trim() || undefined,
    page: 1,
    page_size: 200,
  })

  const sorted = React.useMemo(() => {
    const items = [...(data?.items ?? [])]
    items.sort((a, b) => compareCandidates(a, b, sortField, sortDir))
    return items
  }, [data, sortField, sortDir])

  function toggleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortField(field)
      setSortDir(field === "name" ? "asc" : "desc")
    }
  }

  const jobMap = React.useMemo(() => {
    const m = new Map<string, string>()
    jobsData?.items.forEach((j) => m.set(j.id, j.title))
    return m
  }, [jobsData])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
          <Users className="h-5 w-5 text-muted-foreground" />
          候选人
        </h2>
        <p className="text-sm text-muted-foreground">
          查看 AI 五维评分结果，点击候选人进入画像详情页
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-base">
            全部候选人（{data?.total ?? 0} 人）
          </CardTitle>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="搜索姓名 / 手机 / 邮箱"
                className="h-8 w-60 pl-7 text-xs"
              />
            </div>
            <Select
              value={jobId ?? ALL_JOB}
              onValueChange={(v) => setJobId(v === ALL_JOB ? undefined : v)}
            >
              <SelectTrigger className="h-8 w-48 text-xs">
                <SelectValue placeholder="按职位过滤" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_JOB}>全部职位</SelectItem>
                {jobsData?.items.map((j) => (
                  <SelectItem key={j.id} value={j.id}>
                    {j.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {jobId ? (
              <ExportMenu
                jobId={jobId}
                jobTitle={jobMap.get(jobId)}
                size="sm"
              />
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex flex-col gap-2 p-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : sorted.length === 0 ? (
            <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
              暂无候选人
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">
                    <SortButton
                      label="姓名"
                      field="name"
                      cur={sortField}
                      dir={sortDir}
                      onToggle={toggleSort}
                    />
                  </TableHead>
                  <TableHead className="w-[120px]">
                    <SortButton
                      label="评分"
                      field="score"
                      cur={sortField}
                      dir={sortDir}
                      onToggle={toggleSort}
                    />
                  </TableHead>
                  <TableHead>联系方式</TableHead>
                  <TableHead>应聘职位</TableHead>
                  <TableHead className="w-[100px]">状态</TableHead>
                  <TableHead className="w-[160px]">
                    <SortButton
                      label="更新时间"
                      field="updated_at"
                      cur={sortField}
                      dir={sortDir}
                      onToggle={toggleSort}
                    />
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sorted.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell>
                      <Link
                        href={`/candidates/${c.id}`}
                        className="font-medium hover:text-primary hover:underline"
                      >
                        {c.name ?? "（未识别）"}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <ScoreBadge score={c.score} size="sm" />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      <div className="flex flex-col gap-0.5">
                        {c.phone && <span>📱 {c.phone}</span>}
                        {c.email && (
                          <span className="truncate">✉ {c.email}</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {jobMap.get(c.job_id) ?? "—"}
                    </TableCell>
                    <TableCell>
                      {c.is_verified ? (
                        <Badge
                          variant="outline"
                          className="gap-1 border-emerald-200 bg-emerald-50 text-[10px] text-emerald-700"
                        >
                          <CheckCircle2 className="h-3 w-3" />
                          已核验
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(c.updated_at).toLocaleString("zh-CN")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function SortButton({
  label,
  field,
  cur,
  dir,
  onToggle,
}: {
  label: string
  field: SortField
  cur: SortField
  dir: SortDir
  onToggle: (f: SortField) => void
}) {
  const active = field === cur
  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-2 h-7 gap-1 px-2 text-xs font-medium"
      onClick={() => onToggle(field)}
    >
      {label}
      <ArrowUpDown
        className={`h-3 w-3 ${active ? "text-foreground" : "text-muted-foreground/40"}`}
      />
      {active && <span className="text-[10px]">{dir === "desc" ? "↓" : "↑"}</span>}
    </Button>
  )
}

function compareCandidates(
  a: Candidate,
  b: Candidate,
  field: SortField,
  dir: SortDir
): number {
  const mul = dir === "desc" ? -1 : 1
  if (field === "score") {
    return mul * ((a.score ?? -1) - (b.score ?? -1))
  }
  if (field === "name") {
    return mul * (a.name ?? "").localeCompare(b.name ?? "")
  }
  return mul * (a.updated_at.localeCompare(b.updated_at))
}
