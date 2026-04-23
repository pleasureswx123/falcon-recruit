import { apiClient } from "@/lib/api/client"

// ===== 类型定义（与后端 schemas/task.py 严格对齐） =====

export type TaskStatus =
  | "pending"
  | "extracting"
  | "parsing"
  | "linking"
  | "succeeded"
  | "failed"

export interface TaskDiagnosticCandidate {
  candidate_id: string
  name: string | null
  phone: string | null
  email: string | null
  file_ids: string[]
  primary_file_id: string | null
  reason: string
}

export interface TaskDiagnostics {
  candidates?: TaskDiagnosticCandidate[]
  unmatched_files?: Array<{
    file_id: string
    original_name: string
    reason: string
  }>
}

export interface SortingTask {
  id: string
  job_id: string
  status: TaskStatus
  stage_message: string | null
  progress: number
  total_files: number
  parsed_files: number
  failed_files: number
  candidate_count: number
  source_zip_name: string
  source_zip_size: number
  error_message: string | null
  diagnostics: TaskDiagnostics
  created_at: string
  updated_at: string
  finished_at: string | null
}

export interface TaskListResponse {
  total: number
  items: SortingTask[]
}

export interface TaskListQuery {
  job_id?: string
  page?: number
  page_size?: number
}

// ===== API 服务 =====

export async function uploadZip(params: {
  job_id: string
  file: File
  onUploadProgress?: (percent: number) => void
}): Promise<SortingTask> {
  const form = new FormData()
  form.append("job_id", params.job_id)
  form.append("file", params.file)
  const { data } = await apiClient.post<SortingTask>(
    "/tasks/upload",
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120_000,
      onUploadProgress: (e) => {
        if (params.onUploadProgress && e.total) {
          params.onUploadProgress(Math.round((e.loaded * 100) / e.total))
        }
      },
    }
  )
  return data
}

export async function getTask(id: string): Promise<SortingTask> {
  const { data } = await apiClient.get<SortingTask>(`/tasks/${id}`)
  return data
}

export async function listTasks(
  params: TaskListQuery = {}
): Promise<TaskListResponse> {
  const { data } = await apiClient.get<TaskListResponse>("/tasks", {
    params,
  })
  return data
}

// ===== 未关联文件（Phase 6） =====

export type FileType = "RESUME" | "PORTFOLIO" | "UNKNOWN"
export type ParseStatus = "pending" | "parsed" | "failed" | "unsupported"

export interface UnmatchedFileItem {
  file_id: string
  original_name: string
  file_type: FileType
  mime: string | null
  size: number
  parse_status: ParseStatus
  parse_error: string | null
  text_excerpt: string | null
  zip_member: string
  candidate_id: string | null
  reason: string
}

export interface UnmatchedFilesResponse {
  task_id: string
  job_id: string
  total: number
  items: UnmatchedFileItem[]
}

export async function getUnmatchedFiles(
  taskId: string
): Promise<UnmatchedFilesResponse> {
  const { data } = await apiClient.get<UnmatchedFilesResponse>(
    `/tasks/${taskId}/unmatched-files`
  )
  return data
}

export const TERMINAL_STATUSES: TaskStatus[] = ["succeeded", "failed"]

export const STATUS_LABEL: Record<TaskStatus, string> = {
  pending: "排队中",
  extracting: "解压中",
  parsing: "解析中",
  linking: "关联中",
  succeeded: "已完成",
  failed: "已失败",
}
