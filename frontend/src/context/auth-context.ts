import { createContext, useContext } from 'react'
import type { User } from '../types/auth'

export interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (code: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
