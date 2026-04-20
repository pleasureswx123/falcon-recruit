"use client"

import {
  Briefcase,
  FileCheck2,
  Loader2,
  TrendingUp,
  Users,
} from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { DashboardStats } from "@/lib/api/dashboard"

interface Props {
  stats: DashboardStats | undefined
  isLoading: boolean
}

export function StatCards({ stats, isLoading }: Props) {
  const items = [
    {
      title: "进行中职位",
      value: stats?.jobs_active ?? 0,
      icon: Briefcase,
      hint: stats
        ? `共 ${stats.jobs_total} 个职位`
        : "—",
    },
    {
      title: "累计候选人",
      value: stats?.candidates_total ?? 0,
      icon: Users,
      hint: stats
        ? `${stats.candidates_unverified} 人待核验`
        : "—",
    },
    {
      title: "高分人才",
      value: stats?.high_score_count ?? 0,
      icon: TrendingUp,
      hint: "AI 评分 ≥ 80",
    },
    {
      title: "运行中任务",
      value: stats?.tasks_running ?? 0,
      icon: stats?.tasks_running ? Loader2 : FileCheck2,
      hint: stats?.tasks_running ? "分拣进行中" : "暂无分拣任务",
      spin: Boolean(stats?.tasks_running),
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {items.map((s) => {
        const Icon = s.icon
        return (
          <Card key={s.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{s.title}</CardTitle>
              <Icon
                className={`h-4 w-4 text-muted-foreground ${
                  s.spin ? "animate-spin" : ""
                }`}
              />
            </CardHeader>
            <CardContent>
              {isLoading && !stats ? (
                <Skeleton className="h-7 w-16" />
              ) : (
                <div className="text-2xl font-bold tabular-nums">{s.value}</div>
              )}
              <p className="text-xs text-muted-foreground">{s.hint}</p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
