/**
 * Authentication hooks using TanStack Query and Zustand
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { login as loginApi, logout as logoutApi, getCurrentUser } from '@/lib/api'
import { useAuthStore } from '@/stores/auth-store'
import { User } from '@/types/auth'

/**
 * Hook to login user
 */
export function useLogin() {
  const router = useRouter()
  const { setUser } = useAuthStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      loginApi(email, password),
    onSuccess: (data) => {
      // Update auth store with user data
      setUser(data.user)

      // Cache the user data
      queryClient.setQueryData(['currentUser'], data.user)

      // Redirect to declarations page
      router.push('/declarations')
    },
    onError: (error) => {
      // Error is handled by the component displaying error message
      void error // Suppress unused variable warning
    },
  })
}

/**
 * Hook to logout user
 */
export function useLogout() {
  const router = useRouter()
  const { clearUser } = useAuthStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: logoutApi,
    onSuccess: () => {
      // Clear auth store
      clearUser()

      // Clear all cached queries
      queryClient.clear()

      // Redirect to login page
      router.push('/login')
    },
    onError: (error) => {
      // Even if logout fails, clear local state and redirect
      void error // Suppress unused variable warning
      clearUser()
      queryClient.clear()
      router.push('/login')
    },
  })
}

/**
 * Hook to fetch current authenticated user
 * This runs on app load to restore session
 */
export function useCurrentUser() {
  const { setUser, clearUser } = useAuthStore()

  const query = useQuery<User, Error>({
    queryKey: ['currentUser'],
    queryFn: getCurrentUser,
    retry: false, // Don't retry on 401
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  })

  // Handle side effects based on query state
  if (query.isSuccess && query.data) {
    setUser(query.data)
  } else if (query.isError) {
    // User is not authenticated or session expired
    clearUser()
  }

  return query
}

/**
 * Hook to check if user is authenticated
 */
export function useAuth() {
  const { user, isAuthenticated, isLoading } = useAuthStore()

  return {
    user,
    isAuthenticated,
    isLoading,
  }
}
