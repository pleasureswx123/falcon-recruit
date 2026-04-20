import { API_BASE_URL, apiClient } from "@/lib/api/client"

export type ExportFormat = "zip" | "csv"

export interface ExportFilter {
  verifiedOnly?: boolean
  minScore?: number | null
}

/** 构造下载 URL（直接由浏览器发起 GET 请求）。 */
export function buildExportUrl(
  format: ExportFormat,
  jobId: string,
  filter: ExportFilter = {}
): string {
  const params = new URLSearchParams()
  if (filter.verifiedOnly) params.set("verified_only", "true")
  if (filter.minScore != null && filter.minScore > 0) {
    params.set("min_score", String(filter.minScore))
  }
  const qs = params.toString()
  const suffix = qs ? `?${qs}` : ""
  return `${API_BASE_URL}/api/export/${format}/${jobId}${suffix}`
}

/** 从 Content-Disposition 中提取 RFC 5987 的 filename*=UTF-8''xxx 部分。 */
function parseDispositionFilename(header: string | undefined): string | null {
  if (!header) return null
  const star = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(header)
  if (star) {
    try {
      return decodeURIComponent(star[1].trim())
    } catch {
      return star[1].trim()
    }
  }
  const ascii = /filename\s*=\s*"?([^";]+)"?/i.exec(header)
  return ascii ? ascii[1].trim() : null
}

/** 通过 XHR 下载 Blob，支持前端捕获 4xx 错误并弹 toast。 */
export async function downloadExport(
  format: ExportFormat,
  jobId: string,
  filter: ExportFilter = {},
  fallbackName?: string
): Promise<{ filename: string; size: number }> {
  const path = `/api/export/${format}/${jobId}`
  const params: Record<string, string> = {}
  if (filter.verifiedOnly) params.verified_only = "true"
  if (filter.minScore != null && filter.minScore > 0) {
    params.min_score = String(filter.minScore)
  }

  const response = await apiClient.get<Blob>(path, {
    params,
    responseType: "blob",
    timeout: 120_000,
  })

  const disposition = response.headers["content-disposition"] as
    | string
    | undefined
  const filename =
    parseDispositionFilename(disposition) ??
    fallbackName ??
    `export.${format}`

  const blob = response.data
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  // 延迟释放，避免 Safari 下载被中断
  setTimeout(() => URL.revokeObjectURL(url), 5_000)

  return { filename, size: blob.size }
}
