"use client"

import * as React from "react"
import Link from "next/link"
import {
  Archive,
  ArchiveRestore,
  Eye,
  MoreHorizontal,
  Pencil,
  Trash2,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { Job } from "@/lib/api/jobs"
import { useUpdateJob } from "@/lib/hooks/use-jobs"

interface Props {
  job: Job
  onEdit: () => void
  onDelete: () => void
}

export function JobsTableRowActions({ job, onEdit, onDelete }: Props) {
  const update = useUpdateJob(job.id)
  const nextStatus = job.status === "active" ? "closed" : "active"

  async function toggleStatus() {
    try {
      await update.mutateAsync({ status: nextStatus })
      toast.success(
        nextStatus === "closed" ? "职位已归档" : "职位已恢复为进行中"
      )
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "操作失败")
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <MoreHorizontal className="h-4 w-4" />
          <span className="sr-only">打开菜单</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>职位操作</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href={`/jobs/${job.id}`}>
            <Eye className="mr-2 h-4 w-4" />
            查看详情
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onEdit}>
          <Pencil className="mr-2 h-4 w-4" />
          编辑
        </DropdownMenuItem>
        <DropdownMenuItem onClick={toggleStatus} disabled={update.isPending}>
          {job.status === "active" ? (
            <>
              <Archive className="mr-2 h-4 w-4" />
              归档为「已结束」
            </>
          ) : (
            <>
              <ArchiveRestore className="mr-2 h-4 w-4" />
              恢复为「进行中」
            </>
          )}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-destructive focus:text-destructive"
          onClick={onDelete}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          删除
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
