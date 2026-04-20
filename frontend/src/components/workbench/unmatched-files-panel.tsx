"use client"

import * as React from "react"
import { AlertTriangle, FileQuestion, Link as LinkIcon } from "lucide-react"

import { ReassignFileDialog } from "@/components/workbench/reassign-file-dialog"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { UnmatchedFileItem } from "@/lib/api/tasks"
import { useUnmatchedFiles } from "@/lib/hooks/use-tasks"

interface Props {
  taskId: string | undefined
  jobId: string
}

const TYPE_LABEL: Record<UnmatchedFileItem["file_type"], string> = {
  RESUME: "简历",
  PORTFOLIO: "作品集",
  UNKNOWN: "附件",
}

export function UnmatchedFilesPanel({ taskId, jobId }: Props) {
  const { data, isLoading, error } = useUnmatchedFiles(taskId)
  const [pending, setPending] = React.useState<UnmatchedFileItem | null>(null)

  if (!taskId) {
    return null
  }

  const items = data?.items ?? []
  const hasItems = items.length > 0

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              未关联文件
              {hasItems && (
                <span className="rounded-md bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-700">
                  {items.length}
                </span>
              )}
            </CardTitle>
            <CardDescription className="text-xs">
              未能自动识别归属的文件，可手动挂到任意候选人
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        )}
        {error && (
          <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            加载失败：{(error as { message?: string })?.message ?? "未知错误"}
          </div>
        )}
        {!isLoading && !error && !hasItems && (
          <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-8 text-center">
            <FileQuestion className="h-6 w-6 text-muted-foreground" />
            <div className="text-xs text-muted-foreground">
              本次任务所有文件均已自动关联
            </div>
          </div>
        )}
        {!isLoading && hasItems && (
          <ul className="space-y-2">
            {items.map((f) => (
              <li
                key={f.file_id}
                className="flex items-start justify-between gap-2 rounded-md border bg-muted/30 px-3 py-2"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium">
                      {f.original_name}
                    </span>
                    <span className="shrink-0 rounded bg-background px-1.5 py-0.5 text-[10px] text-muted-foreground">
                      {TYPE_LABEL[f.file_type]}
                    </span>
                  </div>
                  <div className="mt-0.5 truncate text-[11px] text-muted-foreground">
                    {f.zip_member}
                  </div>
                  <div className="mt-1 text-[11px] text-amber-700">
                    {f.reason}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="shrink-0"
                  onClick={() => setPending(f)}
                >
                  <LinkIcon className="mr-1 h-3.5 w-3.5" />
                  挂载
                </Button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>

      {pending && (
        <ReassignFileDialog
          open={Boolean(pending)}
          onOpenChange={(open) => !open && setPending(null)}
          fileId={pending.file_id}
          jobId={jobId}
          excludeCandidateId={pending.candidate_id ?? undefined}
        />
      )}
    </Card>
  )
}
