import type { ReactNode } from 'react'
import { Navigate } from 'react-router'
import { useAuth } from '../context/auth-context'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <p>Loading…</p>
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return children
}
