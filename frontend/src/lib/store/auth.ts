import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface User {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  login: (user: User) => void
  logout: () => void
  setUser: (user: User | null) => void
  // 添加版本号，用于触发缓存失效
  version: number
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      version: 0,
      login: (user) => set((state) => ({ user, isAuthenticated: true, version: state.version + 1 })),
      logout: () => set((state) => ({ user: null, isAuthenticated: false, version: state.version + 1 })),
      setUser: (user) => set((state) => ({ user, isAuthenticated: !!user, version: state.version + 1 })),
    }),
    { name: 'auth-storage' }
  )
)
