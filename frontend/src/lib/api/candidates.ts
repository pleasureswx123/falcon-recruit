import { apiClient, API_BASE_URL } from "@/lib/api/client"

// ===== 类型定义（与后端 schemas/candidate.py 严格对齐） =====

export type FileType = "RESUME" | "PORTFOLIO" | "UNKNOWN"
export type ParseStatus = "pending" | "parsed" | "failed" | "unsupported"

export interface CandidateFile {
  id: string
  file_type: FileType
  original_name: string
  new_name: string | null
  mime: string | null
  size: number
  parse_status: ParseStatus
  parse_error: string | null
  text_excerpt: string | null
  zip_member: string
}

export interface Candidate {
  id: string
  job_id: string
  name: string | null
  phone: string | null
  email: string | null
  wechat: string | null
  score: number | null
  report: Record<string, unknown>
  is_verified: boolean
  created_at: string
  updated_at: string
}

export interface CandidateDetail extends Candidate {
  files: CandidateFile[]
}

export interface CandidateListResponse {
  total: number
  items: Candidate[]
}

export interface CandidateListQuery {
  job_id?: string
  keyword?: string
  verified?: boolean
  page?: number
  page_size?: number
}

export interface CandidateUpdatePayload {
  name?: string | null
  phone?: string | null
  email?: string | null
  wechat?: string | null
  is_verified?: boolean
}

// ===== API 服务 =====

export async function listCandidates(
  params: CandidateListQuery = {}
): Promise<CandidateListResponse> {
  const { data } = await apiClient.get<CandidateListResponse>(
    "/candidates",
    { params }
  )
  return data
}

export async function getCandidate(id: string): Promise<CandidateDetail> {
  const { data } = await apiClient.get<CandidateDetail>(
    `/candidates/${id}`
  )
  return data
}

export async function updateCandidate(
  id: string,
  payload: CandidateUpdatePayload
): Promise<Candidate> {
  const { data } = await apiClient.patch<Candidate>(
    `/candidates/${id}`,
    payload
  )
  return data
}

export async function reassignFile(params: {
  candidate_id: string
  file_id: string
}): Promise<CandidateFile> {
  const { data } = await apiClient.post<CandidateFile>(
    `/candidates/${params.candidate_id}/files/${params.file_id}`
  )
  return data
}

// ===== 下载 / 预览 URL 工具 =====

export function fileDownloadUrl(fileId: string, rename = true): string {
  const q = rename ? "" : "?rename=false"
  return `${API_BASE_URL}/files/${fileId}/download${q}`
}

export function filePreviewUrl(fileId: string): string {
  return `${API_BASE_URL}/files/${fileId}/preview`
}

// ===== 显示工具 =====

export const FILE_TYPE_LABEL: Record<FileType, string> = {
  RESUME: "简历",
  PORTFOLIO: "作品集",
  UNKNOWN: "未识别",
}

export const PARSE_STATUS_LABEL: Record<ParseStatus, string> = {
  pending: "待解析",
  parsed: "已解析",
  failed: "解析失败",
  unsupported: "不支持",
}
