"use client"

import Link from "next/link"
import { ArrowRight, X } from "lucide-react"

import { TaskStatusBadge } from "@/components/sorting/task-status-badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import type { SortingTask } from "@/lib/api/tasks"

interface Props {
  task: SortingTask
  onDismiss?: () => void
}

export function SortingTaskCard({ task, onDismiss }: Props) {
  const isTerminal = task.status === "succeeded" || task.status === "failed"

  return (
    <div className="flex flex-col gap-3 rounded-lg border bg-muted/30 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate text-sm font-medium">
              {task.source_zip_name}
            </span>
            <TaskStatusBadge status={task.status} />
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {task.stage_message ?? "等待调度…"}
          </div>
        </div>
        {onDismiss && isTerminal && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={onDismiss}
          >
            <X className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>进度</span>
          <span>{task.progress}%</span>
        </div>
        <Progress value={task.progress} className="h-1.5" />
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <Stat label="已解析" value={task.parsed_files} total={task.total_files} />
        <Stat label="失败" value={task.failed_files} tone="warn" />
        <Stat label="候选人" value={task.candidate_count} tone="ok" />
      </div>

      {task.status === "failed" && task.error_message && (
        <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-xs text-destructive">
          {task.error_message}
        </div>
      )}

      {task.status === "succeeded" && (
        <Button variant="outline" size="sm" asChild>
          <Link href={`/workbench?jobId=${task.job_id}&taskId=${task.id}`}>
            查看分拣结果
            <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </Link>
        </Button>
      )}
    </div>
  )
}

function Stat({
  label,
  value,
  total,
  tone,
}: {
  label: string
  value: number
  total?: number
  tone?: "ok" | "warn"
}) {
  const color =
    tone === "ok"
      ? "text-emerald-600"
      : tone === "warn"
      ? "text-amber-600"
      : "text-foreground"
  return (
    <div className="rounded-md border bg-background px-2 py-1.5">
      <div className={`text-lg font-semibold ${color}`}>
        {value}
        {typeof total === "number" && (
          <span className="text-xs font-normal text-muted-foreground">
            {" "}
            / {total}
          </span>
        )}
      </div>
      <div className="text-[11px] text-muted-foreground">{label}</div>
    </div>
  )
}
