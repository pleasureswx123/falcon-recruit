import { apiClient } from "@/lib/api/client"
import type { TaskStatus } from "@/lib/api/tasks"

export interface DashboardStats {
  jobs_total: number
  jobs_active: number
  candidates_total: number
  candidates_unverified: number
  high_score_count: number
  tasks_running: number
}

export interface TopCandidate {
  id: string
  job_id: string
  job_title: string | null
  name: string | null
  score: number | null
  phone: string | null
  email: string | null
  is_verified: boolean
  updated_at: string
}

export interface RecentTask {
  id: string
  job_id: string
  job_title: string | null
  status: TaskStatus
  progress: number
  stage_message: string | null
  total_files: number
  parsed_files: number
  failed_files: number
  candidate_count: number
  source_zip_name: string
  created_at: string
  finished_at: string | null
}

export interface DashboardOverview {
  stats: DashboardStats
  top_candidates: TopCandidate[]
  recent_tasks: RecentTask[]
}

export async function getDashboardOverview(params: {
  top_limit?: number
  recent_limit?: number
} = {}): Promise<DashboardOverview> {
  const { data } = await apiClient.get<DashboardOverview>(
    "/api/dashboard/overview",
    { params }
  )
  return data
}
