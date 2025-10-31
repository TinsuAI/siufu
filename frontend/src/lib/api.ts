/**
 * API client for backend communication
 */

import { LoginResponse, User } from '@/types/auth'
import type { RegisterRequest } from '@/types/auth'
import type { FileUploadState, UploadResponse, UploadErrorResponse } from '@/types/upload'

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

// ==================== Declarations API ====================

/**
 * Upload declaration files to backend
 * @param files - Object containing all 6 required files
 * @returns Declaration ID and metadata
 * @throws Error with user-friendly message on validation or upload failure
 */
export async function uploadDeclaration(files: FileUploadState): Promise<UploadResponse> {
  // Build FormData object with correct field names matching backend API
  const formData = new FormData()

  if (files.arrival_notice) formData.append('arrival_notice', files.arrival_notice)
  if (files.bill_of_lading) formData.append('bill_of_lading', files.bill_of_lading)
  if (files.certificate_of_origin) formData.append('certificate_of_origin', files.certificate_of_origin)
  if (files.invoice) formData.append('invoice', files.invoice)
  if (files.good_list) formData.append('good_list', files.good_list)
  if (files.exim_tariff) formData.append('exim_tariff', files.exim_tariff)

  const url = `${API_BASE_URL}/declarations/upload`

  // Create AbortController for timeout handling (60 seconds)
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60000)

  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      credentials: 'include', // Include cookies for authentication
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      // Parse error response following RFC 7807 Problem Details format
      const errorData: UploadErrorResponse = await response.json().catch(() => ({
        type: 'UnknownError',
        title: 'Upload failed',
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }))

      // Extract user-friendly error message
      let errorMessage = errorData.detail || 'Failed to upload files'

      // If there are invalid params, include them in the error message
      if (errorData.invalid_params && errorData.invalid_params.length > 0) {
        const paramErrors = errorData.invalid_params
          .map((param) => `${param.name}: ${param.reason}`)
          .join(', ')
        errorMessage = `${errorData.title}: ${paramErrors}`
      }

      throw new Error(errorMessage)
    }

    return response.json()
  } catch (error) {
    clearTimeout(timeoutId)

    // Handle timeout error
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Upload timeout. Please check your connection and try again.')
    }

    // Handle network errors
    if (error instanceof Error && error.message.includes('fetch')) {
      throw new Error('Network error. Please check your connection and try again.')
    }

    // Re-throw other errors
    throw error
  }
}
