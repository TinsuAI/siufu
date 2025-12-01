/**
 * Unit tests for authentication hooks
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useRouter } from '@/navigation'
import { useLogin, useLogout, useCurrentUser, useAuth } from '@/hooks/use-auth'
import { useAuthStore } from '@/stores/auth-store'
import * as api from '@/lib/api'
import type { User } from '@/types/auth'

// Mock the API module
vi.mock('@/lib/api', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
}))

// Mock @/navigation (localized router)
vi.mock('@/navigation', () => ({
  useRouter: vi.fn(),
}))

describe('useAuth hooks', () => {
  let queryClient: QueryClient
  const mockPush = vi.fn()
  const mockUser: User = {
    id: 'user-123',
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'processor',
    is_active: true,
    organization_id: 'org-123',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  // Store original window.location
  const originalLocation = window.location

  beforeEach(() => {
    // Create a new QueryClient for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
        mutations: {
          retry: false,
        },
      },
    })

    // Mock router
    vi.mocked(useRouter).mockReturnValue({
      push: mockPush,
    } as unknown as ReturnType<typeof useRouter>)

    // Mock window.location for hard redirects
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { ...originalLocation, href: '' },
    })

    // Reset auth store
    useAuthStore.getState().clearUser()
  })

  afterEach(() => {
    // Restore original window.location
    Object.defineProperty(window, 'location', {
      writable: true,
      value: originalLocation,
    })
    queryClient.clear()
    vi.clearAllMocks()
  })

  const wrapper = ({
    children,
  }: {
    children: React.ReactNode
  }): React.JSX.Element => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('useLogin', () => {
    it('should login successfully and redirect to declarations', async () => {
      const mockLoginResponse = {
        user: mockUser,
        access_token: 'mock-token',
        token_type: 'bearer' as const,
      }

      vi.mocked(api.login).mockResolvedValue(mockLoginResponse)

      const { result } = renderHook(() => useLogin(), { wrapper })

      // Trigger login
      result.current.mutate({ email: 'test@example.com', password: 'password' })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify API was called
      expect(api.login).toHaveBeenCalledWith('test@example.com', 'password')

      // Verify auth store was updated
      expect(useAuthStore.getState().user).toEqual(mockUser)

      // Verify hard redirect happened (useLogin uses window.location.href for middleware re-evaluation)
      expect(window.location.href).toBe('/declarations')
    })

    it('should handle login error', async () => {
      const mockError = new Error('Invalid credentials')
      vi.mocked(api.login).mockRejectedValue(mockError)

      const { result } = renderHook(() => useLogin(), { wrapper })

      result.current.mutate({ email: 'test@example.com', password: 'wrong' })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(mockError)
      expect(useAuthStore.getState().user).toBeNull()
    })
  })

  describe('useLogout', () => {
    it('should logout successfully and redirect to login', async () => {
      // Set initial user
      useAuthStore.getState().setUser(mockUser)

      vi.mocked(api.logout).mockResolvedValue()

      const { result } = renderHook(() => useLogout(), { wrapper })

      result.current.mutate()

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify API was called
      expect(api.logout).toHaveBeenCalled()

      // Verify auth store was cleared
      expect(useAuthStore.getState().user).toBeNull()

      // Verify redirect happened
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    it('should clear state and redirect even if logout API fails', async () => {
      // Set initial user
      useAuthStore.getState().setUser(mockUser)

      const mockError = new Error('Network error')
      vi.mocked(api.logout).mockRejectedValue(mockError)

      const { result } = renderHook(() => useLogout(), { wrapper })

      result.current.mutate()

      await waitFor(() => expect(result.current.isError).toBe(true))

      // Verify auth store was cleared even on error
      expect(useAuthStore.getState().user).toBeNull()

      // Verify redirect happened even on error
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  describe('useCurrentUser', () => {
    it('should fetch current user and update store on success', async () => {
      vi.mocked(api.getCurrentUser).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useCurrentUser(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Verify API was called
      expect(api.getCurrentUser).toHaveBeenCalled()

      // Verify auth store was updated
      expect(useAuthStore.getState().user).toEqual(mockUser)

      // Verify hook returns user data
      expect(result.current.data).toEqual(mockUser)
    })

    it('should clear user from store on authentication error', async () => {
      // Set initial user
      useAuthStore.getState().setUser(mockUser)

      const mockError = new Error('Unauthorized')
      vi.mocked(api.getCurrentUser).mockRejectedValue(mockError)

      const { result } = renderHook(() => useCurrentUser(), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))

      // Verify auth store was cleared
      expect(useAuthStore.getState().user).toBeNull()
    })
  })

  describe('useAuth', () => {
    it('should return auth state from store', () => {
      // Set user in store
      useAuthStore.getState().setUser(mockUser)

      const { result } = renderHook(() => useAuth())

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.isLoading).toBe(false)
    })

    it('should return unauthenticated state when no user', () => {
      useAuthStore.getState().clearUser()

      const { result } = renderHook(() => useAuth())

      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.isLoading).toBe(false)
    })
  })
})
