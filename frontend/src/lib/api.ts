/**
 * API client for backend communication
 */

import { LoginResponse, User } from '@/types/auth'
import type { RegisterRequest } from '@/types/auth'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export interface HealthStatus {
  status: string
  version?: string
  timestamp?: string
}

/**
 * Get backend health status
 */
export async function getHealthStatus(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`)
  if (!response.ok) {
    throw new Error('Failed to fetch health status')
  }
  return response.json()
}

/**
 * Generic API fetch wrapper with error handling
 */
export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const defaultHeaders = {
    'Content-Type': 'application/json',
  }

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options?.headers,
    },
    credentials: 'include', // Always include cookies for authentication
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: 'An error occurred',
    }))
    throw new Error(error.message || `HTTP ${response.status}`)
  }

  return response.json()
}

// ==================== Authentication API ====================

/**
 * Login user with email and password
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiClient<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

/**
 * Register new user account
 */
export async function register(data: RegisterRequest): Promise<LoginResponse> {
  return apiClient<LoginResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Logout current user (clears cookie)
 */
export async function logout(): Promise<void> {
  await apiClient<{ message: string }>('/auth/logout', {
    method: 'POST',
  })
}

/**
 * Get current authenticated user profile
 */
export async function getCurrentUser(): Promise<User> {
  return apiClient<User>('/auth/me', {
    method: 'GET',
  })
}
