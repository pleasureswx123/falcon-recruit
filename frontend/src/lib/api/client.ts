import axios, { type AxiosError, type AxiosInstance } from "axios"

/**
 * API 基础 URL 配置
 * 
 * 统一使用 /api 前缀，通过代理层转发到后端
 */
export const API_BASE_URL = "/api"

export interface ApiError {
  status: number
  code?: string
  message: string
  detail?: unknown
  requestId?: string
}

function createClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15_000,
    headers: {
      "Content-Type": "application/json",
    },
    // 允许携带 Cookie
    withCredentials: true,
  })

  instance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError<{ detail?: unknown; message?: string; request_id?: string }>) => {
      const status = error.response?.status ?? 0
      const data = error.response?.data
      const requestId =
        (data && typeof data.request_id === "string" ? data.request_id : undefined) ??
        (error.response?.headers?.["x-request-id"] as string | undefined)

      // 401：清除本地用户状态并重定向到登录页
      if (status === 401 && typeof window !== "undefined") {
        // 动态导入避免循环依赖
        import("@/lib/store/auth").then(({ useAuthStore }) => {
          useAuthStore.getState().logout()
          window.location.href = "/login"
        })
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
