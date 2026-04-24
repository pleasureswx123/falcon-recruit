"use client"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"

import type { ApiError } from "@/lib/api/client"
import {
  getDashboardOverview,
  type DashboardOverview,
} from "@/lib/api/dashboard"
import { useAuthStore } from "@/lib/store/auth"

export function useDashboardOverview(params: {
  top_limit?: number
  recent_limit?: number
} = {}) {
  const authVersion = useAuthStore((state) => state.version)
  const queryClient = useQueryClient()
  
  // 当用户切换时，失效 dashboard 缓存
  useEffect(() => {
    queryClient.invalidateQueries({ queryKey: ["dashboard"] })
  }, [authVersion, queryClient])
  
  return useQuery<DashboardOverview, ApiError>({
    queryKey: ["dashboard", "overview", params],
    queryFn: () => getDashboardOverview(params),
    refetchInterval: 15_000,
    staleTime: 5_000,
  })
}
