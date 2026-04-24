import { apiClient } from './client'
import type { User } from '@/lib/store/auth'

export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    apiClient.post<User>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<User>('/auth/login', data),

  logout: () =>
    apiClient.post('/auth/logout'),

  getCurrentUser: () =>
    apiClient.get<User>('/auth/me'),
}
