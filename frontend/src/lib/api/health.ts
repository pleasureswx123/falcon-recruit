import { apiClient } from "@/lib/api/client"

export interface HealthResponse {
  status: string
  app_name: string
  app_env: string
  app_version: string
  server_time: string
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>("/health")
  return data
}
