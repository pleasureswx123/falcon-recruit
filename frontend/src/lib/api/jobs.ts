import { apiClient } from "@/lib/api/client"

// ===== 类型定义（与后端 schemas/job.py 严格对齐） =====

export type JobStatus = "active" | "closed"
export type EducationLevel =
  | "unlimited"
  | "college"
  | "bachelor"
  | "master"
  | "phd"
export type SkillLevel = "required" | "preferred" | "bonus"

export interface SkillRequirement {
  name: string
  level: SkillLevel
  weight: number
}

export interface SalaryRange {
  min: number | null
  max: number | null
}

export interface JobCriteria {
  education: EducationLevel
  years_min: number
  years_max: number | null
  skills: SkillRequirement[]
  industries: string[]
  min_tenure_months: number | null
  soft_skills: string[]
  salary: SalaryRange
  location: string | null
}

export interface Job {
  id: string
  title: string
  raw_jd: string
  criteria: JobCriteria
  status: JobStatus
  created_at: string
  updated_at: string
}

export interface JobListResponse {
  total: number
  items: Job[]
}

export interface JobListQuery {
  status?: JobStatus
  keyword?: string
  page?: number
  page_size?: number
}

export interface JobCreatePayload {
  title: string
  raw_jd: string
  criteria?: JobCriteria | null
  status?: JobStatus
}

export type JobUpdatePayload = Partial<
  Pick<Job, "title" | "raw_jd" | "criteria" | "status">
>

// ===== API 服务 =====

export async function listJobs(
  params: JobListQuery = {}
): Promise<JobListResponse> {
  const { data } = await apiClient.get<JobListResponse>("/api/jobs", {
    params,
  })
  return data
}

export async function getJob(id: string): Promise<Job> {
  const { data } = await apiClient.get<Job>(`/api/jobs/${id}`)
  return data
}

export async function createJob(payload: JobCreatePayload): Promise<Job> {
  const { data } = await apiClient.post<Job>("/api/jobs", payload)
  return data
}

export async function updateJob(
  id: string,
  payload: JobUpdatePayload
): Promise<Job> {
  const { data } = await apiClient.patch<Job>(`/api/jobs/${id}`, payload)
  return data
}

export async function deleteJob(id: string): Promise<void> {
  await apiClient.delete(`/api/jobs/${id}`)
}

export async function parseJd(raw_jd: string): Promise<JobCriteria> {
  const { data } = await apiClient.post<{ criteria: JobCriteria }>(
    "/api/jobs/parse-jd",
    { raw_jd }
  )
  return data.criteria
}

export interface GenerateJdPayload {
  title: string
  description: string
}

export async function generateJd(payload: GenerateJdPayload): Promise<string> {
  const { data } = await apiClient.post<{ jd_text: string }>(
    "/api/jobs/generate-jd",
    payload
  )
  return data.jd_text
}
