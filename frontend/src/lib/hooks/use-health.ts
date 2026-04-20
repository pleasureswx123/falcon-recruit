"use client"

import { useQuery } from "@tanstack/react-query"

import { getHealth, type HealthResponse } from "@/lib/api/health"
import type { ApiError } from "@/lib/api/client"

export function useHealth() {
  return useQuery<HealthResponse, ApiError>({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
    staleTime: 10_000,
  })
}
