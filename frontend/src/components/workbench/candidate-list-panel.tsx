"use client"

import * as React from "react"
import Link from "next/link"
import { CheckCircle2, ExternalLink, Search, User } from "lucide-react"

import { ScoreBadge } from "@/components/reports/score-badge"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { useCandidates } from "@/lib/hooks/use-candidates"
import { cn } from "@/lib/utils"

interface Props {
  jobId: string
  selectedId?: string
  onSelect: (id: string) => void
}

export function CandidateListPanel({ jobId, selectedId, onSelect }: Props) {
  const [keyword, setKeyword] = React.useState("")
  const { data, isLoading } = useCandidates({
    job_id: jobId,
    keyword: keyword.trim() || undefined,
    page: 1,
    page_size: 200,
  })

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <User className="h-4 w-4 text-muted-foreground" />
            候选人
          </span>
          <span className="text-xs font-normal text-muted-foreground">
            {data?.total ?? 0} 人
          </span>
        </CardTitle>
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索姓名 / 手机 / 邮箱"
            className="h-8 pl-7 text-xs"
          />
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[560px]">
          {isLoading ? (
            <div className="flex flex-col gap-2 p-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : !data?.items.length ? (
            <div className="flex h-40 items-center justify-center text-xs text-muted-foreground">
              暂无候选人
            </div>
          ) : (
            <div className="flex flex-col">
              {[...data.items]
                .sort(
                  (a, b) =>
                    (b.score ?? -1) - (a.score ?? -1) ||
                    (a.name ?? "").localeCompare(b.name ?? "")
                )
                .map((c) => (
                  <div
                    key={c.id}
                    className={cn(
                      "group relative flex flex-col gap-1 border-b px-3 py-2.5 text-left transition hover:bg-muted/50",
                      selectedId === c.id && "bg-primary/5 hover:bg-primary/5"
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => onSelect(c.id)}
                      className="absolute inset-0"
                      aria-label={`选择候选人 ${c.name ?? ""}`}
                    />
                    <div className="relative flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-medium">
                        {c.name ?? "（未识别姓名）"}
                      </span>
                      <div className="flex shrink-0 items-center gap-1.5">
                        <ScoreBadge score={c.score} size="sm" showLabel={false} />
                        {c.is_verified && (
                          <Badge
                            variant="outline"
                            className="gap-1 border-emerald-200 bg-emerald-50 text-[10px] text-emerald-700"
                          >
                            <CheckCircle2 className="h-3 w-3" /> 已核
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="relative flex items-center justify-between gap-2">
                      <div className="flex flex-1 flex-wrap gap-x-3 text-[11px] text-muted-foreground">
                        {c.phone && <span>📱 {c.phone}</span>}
                        {c.email && (
                          <span className="truncate">✉ {c.email}</span>
                        )}
                      </div>
                      <Link
                        href={`/candidates/${c.id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="relative z-10 opacity-0 transition group-hover:opacity-100"
                        aria-label="查看评分详情"
                        title="查看评分详情"
                      >
                        <ExternalLink className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                      </Link>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
