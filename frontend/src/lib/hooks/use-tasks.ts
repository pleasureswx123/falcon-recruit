"use client"

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { useEffect, useState } from "react"

import type { ApiError } from "@/lib/api/client"
import {
  type SortingTask,
  type TaskListQuery,
  type TaskListResponse,
  type UnmatchedFilesResponse,
  TERMINAL_STATUSES,
  getTask,
  getUnmatchedFiles,
  listTasks,
  uploadZip,
} from "@/lib/api/tasks"
import { useAuthStore } from "@/lib/store/auth"

const QK = {
  all: ["tasks"] as const,
  list: (q: TaskListQuery) => ["tasks", "list", q] as const,
  detail: (id: string) => ["tasks", "detail", id] as const,
  unmatched: (id: string) => ["tasks", "unmatched", id] as const,
}

export function useTasks(query: TaskListQuery = {}) {
  const authVersion = useAuthStore((state) => state.version)
  const queryClient = useQueryClient()
  const [isVisible, setIsVisible] = useState(true)
  
  // 页面可见性检测
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(document.visibilityState === 'visible')
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])
  
  // 用户切换时失效缓存
  useEffect(() => {
    queryClient.invalidateQueries({ queryKey: QK.all })
  }, [authVersion, queryClient])
  
  return useQuery<TaskListResponse, ApiError>({
    queryKey: QK.list(query),
    queryFn: () => listTasks(query),
    placeholderData: keepPreviousData,
    refetchInterval: (query) => {
      // 1. 页面不可见时不轮询
      if (!isVisible) return false
      
      // 2. 没有数据时保持轮询
      const data = query.state.data
      if (!data || !data.items) return 3000
      
      // 3. 检查是否有活跃任务（pending/processing）
      const hasActiveTask = data.items.some(
        (task) => !TERMINAL_STATUSES.includes(task.status)
      )
      
      // 4. 有活跃任务才轮询，否则停止
      return hasActiveTask ? 3000 : false
    },
  })
}

/**
 * 轮询单个任务直到终态。polling 间隔 1500ms，终态后停止。
 */
export function useTask(id: string | undefined) {
  return useQuery<SortingTask, ApiError>({
    queryKey: QK.detail(id ?? ""),
    queryFn: () => getTask(id as string),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 1500
      return TERMINAL_STATUSES.includes(data.status) ? false : 1500
    },
  })
}

export interface UploadZipVars {
  job_id: string
  file: File
  onUploadProgress?: (percent: number) => void
}

export function useUploadZip() {
  const qc = useQueryClient()
  return useMutation<SortingTask, ApiError, UploadZipVars>({
    mutationFn: (vars) => uploadZip(vars),
    onSuccess: (task) => {
      qc.setQueryData(QK.detail(task.id), task)
      void qc.invalidateQueries({ queryKey: QK.all })
      void qc.invalidateQueries({ queryKey: ["candidates"] })
    },
  })
}

/**
 * 任务内的孤立文件列表（无 PII 候选人或无关联）。用于工作台的「未关联文件」面板。
 */
export function useUnmatchedFiles(taskId: string | undefined) {
  return useQuery<UnmatchedFilesResponse, ApiError>({
    queryKey: QK.unmatched(taskId ?? ""),
    queryFn: () => getUnmatchedFiles(taskId as string),
    enabled: Boolean(taskId),
  })
}
