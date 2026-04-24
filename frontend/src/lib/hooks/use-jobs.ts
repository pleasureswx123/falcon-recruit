"use client"

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { useEffect } from "react"

import type { ApiError } from "@/lib/api/client"
import {
  type GenerateJdPayload,
  type Job,
  type JobCreatePayload,
  type JobCriteria,
  type JobListQuery,
  type JobListResponse,
  type JobUpdatePayload,
  createJob,
  deleteJob,
  generateJd,
  getJob,
  listJobs,
  parseJd,
  updateJob,
} from "@/lib/api/jobs"
import { useAuthStore } from "@/lib/store/auth"

const QK = {
  all: ["jobs"] as const,
  list: (q: JobListQuery) => ["jobs", "list", q] as const,
  detail: (id: string) => ["jobs", "detail", id] as const,
}

export function useJobs(query: JobListQuery = {}) {
  const authVersion = useAuthStore((state) => state.version)
  const queryClient = useQueryClient()
  
  // 当用户切换时，失效所有 jobs 缓存
  useEffect(() => {
    queryClient.invalidateQueries({ queryKey: QK.all })
  }, [authVersion, queryClient])
  
  return useQuery<JobListResponse, ApiError>({
    queryKey: QK.list(query),
    queryFn: () => listJobs(query),
    placeholderData: keepPreviousData,
  })
}

export function useJob(id: string | undefined) {
  return useQuery<Job, ApiError>({
    queryKey: QK.detail(id ?? ""),
    queryFn: () => getJob(id as string),
    enabled: Boolean(id),
  })
}

export function useCreateJob() {
  const qc = useQueryClient()
  return useMutation<Job, ApiError, JobCreatePayload>({
    mutationFn: (payload) => createJob(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QK.all })
    },
  })
}

export function useUpdateJob(id: string) {
  const qc = useQueryClient()
  return useMutation<Job, ApiError, JobUpdatePayload>({
    mutationFn: (payload) => updateJob(id, payload),
    onSuccess: (data) => {
      qc.setQueryData(QK.detail(id), data)
      void qc.invalidateQueries({ queryKey: QK.all })
    },
  })
}

export function useDeleteJob() {
  const qc = useQueryClient()
  return useMutation<void, ApiError, string>({
    mutationFn: (id) => deleteJob(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QK.all })
    },
  })
}

export function useParseJd() {
  return useMutation<JobCriteria, ApiError, string>({
    mutationFn: (raw_jd) => parseJd(raw_jd),
  })
}

export function useGenerateJd() {
  return useMutation<string, ApiError, GenerateJdPayload>({
    mutationFn: (payload) => generateJd(payload),
  })
}
