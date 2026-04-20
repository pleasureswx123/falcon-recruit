"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft, Clock, Pencil, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { ExportMenu } from "@/components/exports/export-menu"
import { JobCriteriaDetail } from "@/components/jobs/job-criteria-detail"
import { JobFormSheet } from "@/components/jobs/job-form-sheet"
import { JobStatusBadge } from "@/components/jobs/job-status-badge"
import { ConfirmDialog } from "@/components/shared/confirm-dialog"
import { SortingPanel } from "@/components/sorting/sorting-panel"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useDeleteJob, useJob } from "@/lib/hooks/use-jobs"

interface Props {
  jobId: string
}

export function JobDetailView({ jobId }: Props) {
  const router = useRouter()
  const { data: job, isLoading, isError, error } = useJob(jobId)
  const deleteMutation = useDeleteJob()

  const [editOpen, setEditOpen] = React.useState(false)
  const [deleteOpen, setDeleteOpen] = React.useState(false)

  async function handleDelete() {
    if (!job) return
    try {
      await deleteMutation.mutateAsync(job.id)
      toast.success(`已删除「${job.title}」`)
      router.push("/jobs")
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "删除失败")
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Skeleton className="h-[400px] lg:col-span-2" />
          <Skeleton className="h-[400px]" />
        </div>
      </div>
    )
  }

  if (isError || !job) {
    return (
      <div className="flex flex-col items-start gap-3">
        <Link
          href="/jobs"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> 返回职位列表
        </Link>
        <div className="rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error?.message ?? "职位不存在或已被删除"}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/jobs"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> 返回职位列表
      </Link>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-semibold tracking-tight">
              {job.title}
            </h2>
            <JobStatusBadge status={job.status} />
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>
              创建于 {new Date(job.created_at).toLocaleString("zh-CN")}
            </span>
            <span className="mx-1">·</span>
            <span>
              更新于 {new Date(job.updated_at).toLocaleString("zh-CN")}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <ExportMenu jobId={job.id} jobTitle={job.title} />
          <Button variant="outline" onClick={() => setEditOpen(true)}>
            <Pencil className="mr-1.5 h-3.5 w-3.5" />
            编辑
          </Button>
          <Button
            variant="outline"
            className="text-destructive hover:text-destructive"
            onClick={() => setDeleteOpen(true)}
          >
            <Trash2 className="mr-1.5 h-3.5 w-3.5" />
            删除
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">JD 原文</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed text-foreground/90">
              {job.raw_jd}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">AI 结构化匹配基准</CardTitle>
          </CardHeader>
          <CardContent>
            <JobCriteriaDetail criteria={job.criteria} />
          </CardContent>
        </Card>
      </div>

      <SortingPanel jobId={job.id} />

      <JobFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        mode="edit"
        job={job}
      />

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={`确认删除「${job.title}」？`}
        description="删除后将无法恢复，关联候选人将解除绑定。"
        confirmText="删除"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </div>
  )
}
