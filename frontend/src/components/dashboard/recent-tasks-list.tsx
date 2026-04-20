"use client"

import Link from "next/link"
import { ListChecks, PackageOpen } from "lucide-react"

import { TaskStatusBadge } from "@/components/sorting/task-status-badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import type { RecentTask } from "@/lib/api/dashboard"

interface Props {
  items: RecentTask[] | undefined
  isLoading: boolean
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return iso
  }
}

export function RecentTasksList({ items, isLoading }: Props) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ListChecks className="h-4 w-4 text-indigo-500" />
          <CardTitle className="text-base">最近分拣任务</CardTitle>
        </div>
        <CardDescription>最新 5 条 ZIP 上传与解析记录</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading && !items ? (
          <div className="flex flex-col gap-2 px-4 pb-4">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : !items || items.length === 0 ? (
          <div className="flex h-32 items-center justify-center gap-2 text-sm text-muted-foreground">
            <PackageOpen className="h-4 w-4" />
            尚未发起分拣任务
          </div>
        ) : (
          <div className="divide-y">
            {items.map((t) => {
              const isRunning =
                t.status === "pending" ||
                t.status === "extracting" ||
                t.status === "parsing" ||
                t.status === "linking"
              const href = isRunning
                ? `/jobs/${t.job_id}`
                : `/workbench?jobId=${t.job_id}&taskId=${t.id}`

              return (
                <Link
                  key={t.id}
                  href={href}
                  className="flex flex-col gap-1.5 px-4 py-3 transition hover:bg-muted/50"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="truncate text-sm font-medium">
                        {t.job_title ?? "（职位已删除）"}
                      </span>
                      <span className="truncate text-xs text-muted-foreground">
                        {t.source_zip_name}
                      </span>
                    </div>
                    <TaskStatusBadge status={t.status} />
                  </div>
                  <div className="flex items-center gap-3">
                    <Progress value={t.progress} className="h-1.5 flex-1" />
                    <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                      {t.candidate_count} 人 · {t.parsed_files}/{t.total_files} 解析
                    </span>
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    {formatTime(t.created_at)}
                    {t.stage_message ? ` · ${t.stage_message}` : ""}
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
