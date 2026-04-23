import axios, { type AxiosError, type AxiosInstance } from "axios"

// 开发环境使用相对路径（通过 Next.js rewrites 代理到后端）
// 生产环境使用环境变量配置的完整 URL
export const API_BASE_URL =
  process.env.NODE_ENV === "development"
    ? ""
    : (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000")

const API_KEY_STORAGE = "falcon_api_key"

export interface ApiError {
  status: number
  code?: string
  message: string
  detail?: unknown
  requestId?: string
}

export function getApiKey(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(API_KEY_STORAGE)
}

export function setApiKey(key: string): void {
  if (typeof window === "undefined") return
  window.localStorage.setItem(API_KEY_STORAGE, key)
}

export function clearApiKey(): void {
  if (typeof window === "undefined") return
  window.localStorage.removeItem(API_KEY_STORAGE)
}

// 401 时仅弹一次 prompt，防止并发请求刷屏
let pendingKeyPrompt: Promise<string | null> | null = null

function promptForApiKey(): Promise<string | null> {
  if (typeof window === "undefined") return Promise.resolve(null)
  const existing = pendingKeyPrompt
  if (existing) return existing
  const task = new Promise<string | null>((resolve) => {
    const input = window.prompt(
      "该接口需要鉴权。请粘贴 Falcon API Key（联系管理员获取）：",
      ""
    )
    if (input && input.trim()) {
      setApiKey(input.trim())
      resolve(input.trim())
    } else {
      resolve(null)
    }
  }).finally(() => {
    pendingKeyPrompt = null
  })
  pendingKeyPrompt = task
  return task
}

function createClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15_000,
    headers: {
      "Content-Type": "application/json",
    },
  })

  instance.interceptors.request.use((config) => {
    const key = getApiKey()
    if (key) {
      config.headers = config.headers ?? {}
      config.headers["X-API-Key"] = key
    }
    return config
  })

  instance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<{ detail?: unknown; message?: string; request_id?: string }>) => {
      const status = error.response?.status ?? 0
      const data = error.response?.data
      const requestId =
        (data && typeof data.request_id === "string" ? data.request_id : undefined) ??
        (error.response?.headers?.["x-request-id"] as string | undefined)

      // 401：清掉旧 key，弹 prompt 让用户补录，并自动重试一次
      if (status === 401 && error.config && !(error.config as { _retried?: boolean })._retried) {
        clearApiKey()
        const newKey = await promptForApiKey()
        if (newKey) {
          const retryConfig = error.config as typeof error.config & { _retried?: boolean }
          retryConfig._retried = true
          retryConfig.headers = retryConfig.headers ?? {}
          retryConfig.headers["X-API-Key"] = newKey
          return instance.request(retryConfig)
        }
      }

      const message =
        (typeof data?.detail === "string" ? data.detail : undefined) ??
        data?.message ??
        error.message ??
        "网络请求失败"

      const apiError: ApiError = {
        status,
        code: error.code,
        message,
        detail: data?.detail,
        requestId,
      }
      return Promise.reject(apiError)
    }
  )

  return instance
}

export const apiClient = createClient()
