"use client"

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import type { ApiError } from "@/lib/api/client"
import {
  type Candidate,
  type CandidateDetail,
  type CandidateFile,
  type CandidateListQuery,
  type CandidateListResponse,
  type CandidateUpdatePayload,
  getCandidate,
  listCandidates,
  reassignFile,
  updateCandidate,
} from "@/lib/api/candidates"

const QK = {
  all: ["candidates"] as const,
  list: (q: CandidateListQuery) => ["candidates", "list", q] as const,
  detail: (id: string) => ["candidates", "detail", id] as const,
}

export function useCandidates(query: CandidateListQuery = {}) {
  return useQuery<CandidateListResponse, ApiError>({
    queryKey: QK.list(query),
    queryFn: () => listCandidates(query),
    placeholderData: keepPreviousData,
  })
}

export function useCandidate(id: string | undefined) {
  return useQuery<CandidateDetail, ApiError>({
    queryKey: QK.detail(id ?? ""),
    queryFn: () => getCandidate(id as string),
    enabled: Boolean(id),
  })
}

export function useUpdateCandidate(id: string) {
  const qc = useQueryClient()
  return useMutation<Candidate, ApiError, CandidateUpdatePayload>({
    mutationFn: (payload) => updateCandidate(id, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QK.detail(id) })
      void qc.invalidateQueries({ queryKey: QK.all })
    },
  })
}

export interface ReassignVars {
  candidate_id: string
  file_id: string
}

export function useReassignFile() {
  const qc = useQueryClient()
  return useMutation<CandidateFile, ApiError, ReassignVars>({
    mutationFn: (vars) => reassignFile(vars),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QK.all })
      void qc.invalidateQueries({ queryKey: ["tasks"] })
    },
  })
}
