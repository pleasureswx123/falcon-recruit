"use client"

import * as React from "react"
import Link from "next/link"
import { Plus, Search } from "lucide-react"
import { toast } from "sonner"

import { JobCriteriaSummary } from "@/components/jobs/job-criteria-summary"
import { JobFormSheet } from "@/components/jobs/job-form-sheet"
import { JobStatusBadge } from "@/components/jobs/job-status-badge"
import { JobsTableRowActions } from "@/components/jobs/jobs-table-row-actions"
import { ConfirmDialog } from "@/components/shared/confirm-dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { Job, JobStatus } from "@/lib/api/jobs"
import { useDeleteJob, useJobs } from "@/lib/hooks/use-jobs"

type StatusFilter = "all" | JobStatus

export function JobsListView() {
  const [statusFilter, setStatusFilter] = React.useState<StatusFilter>("all")
  const [keyword, setKeyword] = React.useState("")
  const [debouncedKeyword, setDebouncedKeyword] = React.useState("")
  const [formOpen, setFormOpen] = React.useState(false)
  const [editingJob, setEditingJob] = React.useState<Job | undefined>()
  const [deletingJob, setDeletingJob] = React.useState<Job | undefined>()

  React.useEffect(() => {
    const t = setTimeout(() => setDebouncedKeyword(keyword.trim()), 300)
    return () => clearTimeout(t)
  }, [keyword])

  const { data, isLoading, isError, error } = useJobs({
    status: statusFilter === "all" ? undefined : statusFilter,
    keyword: debouncedKeyword || undefined,
    page: 1,
    page_size: 50,
  })

  const deleteMutation = useDeleteJob()

  async function handleDelete() {
    if (!deletingJob) return
    try {
      await deleteMutation.mutateAsync(deletingJob.id)
      toast.success(`已删除「${deletingJob.title}」`)
      setDeletingJob(undefined)
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "删除失败")
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">职位管理</h2>
            <p className="text-sm text-muted-foreground">
              创建职位并生成 AI 结构化匹配基准
            </p>
          </div>
          <Button
            onClick={() => {
              setEditingJob(undefined)
              setFormOpen(true)
            }}
          >
            <Plus className="mr-1.5 h-4 w-4" />
            创建职位
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Tabs
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as StatusFilter)}
        >
          <TabsList>
            <TabsTrigger value="all">全部</TabsTrigger>
            <TabsTrigger value="active">进行中</TabsTrigger>
            <TabsTrigger value="closed">已结束</TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="relative w-full sm:w-72">
          <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="按职位名称搜索"
            className="pl-8"
          />
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[28%]">职位名称</TableHead>
              <TableHead className="w-[12%]">状态</TableHead>
              <TableHead>AI 匹配基准</TableHead>
              <TableHead className="w-[160px]">创建时间</TableHead>
              <TableHead className="w-[80px] text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">
                  加载中…
                </TableCell>
              </TableRow>
            )}
            {isError && (
              <TableRow>
                <TableCell colSpan={5} className="py-10 text-center text-destructive">
                  {error?.message ?? "加载失败"}
                </TableCell>
              </TableRow>
            )}
            {!isLoading && !isError && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">
                  暂无职位，点击右上角「创建职位」开始
                </TableCell>
              </TableRow>
            )}
            {data?.items.map((job) => (
              <TableRow key={job.id}>
                <TableCell className="font-medium">
                  <Link
                    href={`/jobs/${job.id}`}
                    className="hover:text-primary hover:underline"
                  >
                    {job.title}
                  </Link>
                </TableCell>
                <TableCell>
                  <JobStatusBadge status={job.status} />
                </TableCell>
                <TableCell>
                  <JobCriteriaSummary criteria={job.criteria} />
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {new Date(job.created_at).toLocaleString("zh-CN")}
                </TableCell>
                <TableCell className="text-right">
                  <JobsTableRowActions
                    job={job}
                    onEdit={() => {
                      setEditingJob(job)
                      setFormOpen(true)
                    }}
                    onDelete={() => setDeletingJob(job)}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <JobFormSheet
        open={formOpen}
        onOpenChange={(o) => {
          setFormOpen(o)
          if (!o) setEditingJob(undefined)
        }}
        mode={editingJob ? "edit" : "create"}
        job={editingJob}
      />

      <ConfirmDialog
        open={Boolean(deletingJob)}
        onOpenChange={(o) => !o && setDeletingJob(undefined)}
        title={`确认删除「${deletingJob?.title ?? ""}」？`}
        description="删除后将无法恢复，关联候选人将解除绑定。"
        confirmText="删除"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={handleDelete}
      />
    </div>
  )
}
