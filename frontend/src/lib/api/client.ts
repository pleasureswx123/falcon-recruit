import axios, { type AxiosError, type AxiosInstance } from "axios"

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"

export interface ApiError {
  status: number
  code?: string
  message: string
  detail?: unknown
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
    // 预留：后续在此注入 Authorization token
    return config
  })

  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError<{ detail?: unknown; message?: string }>) => {
      const status = error.response?.status ?? 0
      const data = error.response?.data
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
      }
      return Promise.reject(apiError)
    }
  )

  return instance
}

export const apiClient = createClient()
