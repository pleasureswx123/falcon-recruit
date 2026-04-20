"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { ApiError } from "@/lib/api/client"
import {
  type CandidateReport,
  getCandidateReport,
} from "@/lib/api/reports"

const QK = {
  report: (id: string) => ["candidates", "report", id] as const,
}

export function useCandidateReport(id: string | undefined) {
  return useQuery<CandidateReport, ApiError>({
    queryKey: QK.report(id ?? ""),
    queryFn: () => getCandidateReport(id as string),
    enabled: Boolean(id),
  })
}

/** 强制重算（refresh=true），成功后刷新缓存。 */
export function useRefreshCandidateReport(id: string) {
  const qc = useQueryClient()
  return useMutation<CandidateReport, ApiError, void>({
    mutationFn: () => getCandidateReport(id, true),
    onSuccess: (data) => {
      qc.setQueryData(QK.report(id), data)
      void qc.invalidateQueries({ queryKey: ["candidates"] })
    },
  })
}
