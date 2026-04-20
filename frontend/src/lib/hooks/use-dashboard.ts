"use client"

import { useQuery } from "@tanstack/react-query"

import type { ApiError } from "@/lib/api/client"
import {
  getDashboardOverview,
  type DashboardOverview,
} from "@/lib/api/dashboard"

export function useDashboardOverview(params: {
  top_limit?: number
  recent_limit?: number
} = {}) {
  return useQuery<DashboardOverview, ApiError>({
    queryKey: ["dashboard", "overview", params],
    queryFn: () => getDashboardOverview(params),
    refetchInterval: 15_000,
    staleTime: 5_000,
  })
}
