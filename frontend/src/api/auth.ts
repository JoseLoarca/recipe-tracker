import { apiClient } from './client'
import type { User } from '../types/auth'

export const authApi = {
  verifyCode: (code: string) => apiClient.post<User>('/api/v1/auth/verify-code', { code }),
  logout: () => apiClient.post<{ status: string }>('/api/v1/auth/logout'),
  me: () => apiClient.get<User>('/api/v1/auth/me'),
}
