"use client"

import Link from "next/link"
import { CheckCircle2, Trophy, TrendingUp } from "lucide-react"

import { ScoreBadge } from "@/components/reports/score-badge"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { TopCandidate } from "@/lib/api/dashboard"

interface Props {
  items: TopCandidate[] | undefined
  isLoading: boolean
}

export function TopCandidatesTable({ items, isLoading }: Props) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Trophy className="h-4 w-4 text-amber-500" />
          <CardTitle className="text-base">高分人才 Top 10</CardTitle>
        </div>
        <CardDescription>
          AI 五维评分最高的候选人，可点击姓名查看完整画像
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading && !items ? (
          <div className="flex flex-col gap-2 px-4 pb-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : !items || items.length === 0 ? (
          <div className="flex h-32 items-center justify-center gap-2 text-sm text-muted-foreground">
            <TrendingUp className="h-4 w-4" />
            暂无已评分候选人
          </div>
        ) : (
          <div className="divide-y">
            {items.map((c, idx) => (
              <Link
                key={c.id}
                href={`/candidates/${c.id}`}
                className="flex items-center gap-3 px-4 py-2.5 transition hover:bg-muted/50"
              >
                <span className="w-6 text-center text-xs font-semibold tabular-nums text-muted-foreground">
                  {idx + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium">
                      {c.name ?? "（未识别）"}
                    </span>
                    {c.is_verified && (
                      <Badge
                        variant="outline"
                        className="h-4 gap-0.5 border-emerald-200 bg-emerald-50 px-1 text-[10px] text-emerald-700"
                      >
                        <CheckCircle2 className="h-2.5 w-2.5" />
                        核验
                      </Badge>
                    )}
                  </div>
                  <div className="truncate text-xs text-muted-foreground">
                    {c.job_title ?? "—"}
                    {c.phone ? ` · ${c.phone}` : ""}
                  </div>
                </div>
                <ScoreBadge score={c.score} size="sm" showLabel={false} />
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
