"use client"

import * as React from "react"
import Link from "next/link"
import { ArrowRight, FileArchive } from "lucide-react"
import { toast } from "sonner"

import { SortingTaskCard } from "@/components/sorting/sorting-task-card"
import { TaskStatusBadge } from "@/components/sorting/task-status-badge"
import { ZipDropzone } from "@/components/sorting/zip-dropzone"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTask, useTasks, useUploadZip } from "@/lib/hooks/use-tasks"

interface Props {
  jobId: string
}

export function SortingPanel({ jobId }: Props) {
  const [activeTaskId, setActiveTaskId] = React.useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = React.useState(0)

  const uploadMutation = useUploadZip()
  const { data: activeTask } = useTask(activeTaskId ?? undefined)
  const { data: taskList, isLoading: isTaskListLoading } = useTasks({
    job_id: jobId,
    page: 1,
    page_size: 5,
  })

  async function handleUpload(file: File) {
    setUploadProgress(0)
    try {
      const task = await uploadMutation.mutateAsync({
        job_id: jobId,
        file,
        onUploadProgress: setUploadProgress,
      })
      setActiveTaskId(task.id)
      toast.success("已提交分拣任务，正在后台处理…")
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "上传失败")
    } finally {
      setUploadProgress(0)
    }
  }

  const latestOtherTasks =
    taskList?.items.filter((t) => t.id !== activeTaskId) ?? []

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <FileArchive className="h-4 w-4 text-muted-foreground" />
          简历分拣
        </CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link href={`/workbench?jobId=${jobId}`}>
            进入工作台
            <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <ZipDropzone
          isUploading={uploadMutation.isPending}
          uploadProgress={uploadProgress}
          onFileSelected={handleUpload}
        />

        {activeTask && (
          <SortingTaskCard
            task={activeTask}
            onDismiss={() => setActiveTaskId(null)}
          />
        )}

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium text-muted-foreground">
              最近任务
            </div>
            <div className="text-xs text-muted-foreground">
              最多显示 5 条
            </div>
          </div>
          {isTaskListLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : latestOtherTasks.length === 0 ? (
            <div className="rounded-md border border-dashed px-3 py-4 text-center text-xs text-muted-foreground">
              暂无历史任务
            </div>
          ) : (
            <div className="flex flex-col divide-y rounded-md border">
              {latestOtherTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between gap-3 px-3 py-2.5 text-sm"
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">
                      {task.source_zip_name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(task.created_at).toLocaleString("zh-CN")} ·{" "}
                      {task.candidate_count} 位候选人 · {task.parsed_files}/
                      {task.total_files} 份文件
                    </div>
                  </div>
                  <TaskStatusBadge status={task.status} />
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
