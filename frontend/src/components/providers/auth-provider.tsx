'use client'

/**
 * Auth Provider - Restores authentication state on app load
 * Fetches current user from API if access_token cookie exists
 */

import { useCurrentUser } from '@/hooks/use-auth'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // This hook fetches the current user from /auth/me and updates the Zustand store
  // It runs once on mount and restores auth state from the httpOnly cookie
  useCurrentUser()

  return <>{children}</>
}
