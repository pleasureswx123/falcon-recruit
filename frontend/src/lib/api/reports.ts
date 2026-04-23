import { apiClient } from "@/lib/api/client"

// ===== 类型定义（严格对齐 backend/app/schemas/profile.py） =====

export type DegreeLevel =
  | "unlimited"
  | "college"
  | "bachelor"
  | "master"
  | "phd"

export type ScoreDimension =
  | "hard_requirements"
  | "professional_background"
  | "stability"
  | "soft_skills"
  | "expectation_fit"

export interface WorkExperience {
  company: string | null
  title: string | null
  start: string | null
  end: string | null
  description: string | null
}

export interface EducationExperience {
  school: string | null
  degree: DegreeLevel
  major: string | null
  start: string | null
  end: string | null
}

export interface ResumeProfile {
  name: string | null
  phone: string | null
  email: string | null
  location: string | null
  expected_salary: string | null
  expected_location: string | null
  total_years: number
  highest_degree: DegreeLevel
  skills: string[]
  soft_skills: string[]
  experiences: WorkExperience[]
  educations: EducationExperience[]
  summary: string | null
}

export interface CareerGap {
  from_end: string | null
  to_start: string | null
  months: number
  is_covered_by_education: boolean
  note: string | null
}

export interface VerificationReport {
  gaps: CareerGap[]
  average_tenure_months: number
  job_hopper: boolean
  risk_flags: string[]
}

export interface DimensionScore {
  dimension: ScoreDimension
  label: string
  score: number
  weight: number
  reason: string
  highlights: string[]
  concerns: string[]
}

export interface InterviewQuestion {
  topic: string
  question: string
  intent?: string | null
}

export interface CandidateReport {
  version: number
  profile: ResumeProfile
  verification: VerificationReport
  dimensions: DimensionScore[]
  total_score: number
  strengths: string[]
  weaknesses: string[]
  interview_questions: InterviewQuestion[]
  generated_at: string | null
  engine: string
}

// ===== API 服务 =====

export async function getCandidateReport(
  candidateId: string,
  refresh = false
): Promise<CandidateReport> {
  const { data } = await apiClient.get<CandidateReport>(
    `/candidates/${candidateId}/report`,
    { params: refresh ? { refresh: true } : {} }
  )
  return data
}

// ===== 显示工具 =====

export const DEGREE_LABEL: Record<DegreeLevel, string> = {
  unlimited: "不限",
  college: "大专",
  bachelor: "本科",
  master: "硕士",
  phd: "博士",
}

export const DIMENSION_ORDER: ScoreDimension[] = [
  "hard_requirements",
  "professional_background",
  "stability",
  "soft_skills",
  "expectation_fit",
]

export function scoreBadgeColor(score: number): {
  bg: string
  fg: string
  label: string
} {
  if (score >= 85) return { bg: "bg-emerald-100", fg: "text-emerald-700", label: "优秀" }
  if (score >= 70) return { bg: "bg-blue-100", fg: "text-blue-700", label: "良好" }
  if (score >= 55) return { bg: "bg-amber-100", fg: "text-amber-700", label: "一般" }
  return { bg: "bg-rose-100", fg: "text-rose-700", label: "偏弱" }
}
