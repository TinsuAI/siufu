/**
 * API client for backend communication
 */

import { LoginResponse, User } from '@/types/auth'
import type { RegisterRequest } from '@/types/auth'
import type {
  FileUploadState,
  UploadResponse,
  UploadErrorResponse,
} from '@/types/upload'
import type {
  StatusResponse,
  RetryProcessingResponse,
} from '@/types/declaration'

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
  const response = await fetch(`${API_BASE_URL}/health`)
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
export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {
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
 * Updated in Story 3.3.1: 4 file types (AN, BOL, CO array, Invoice)
 * @param files - Object containing all 4 required file types (CO supports multiple files)
 * @returns Declaration ID and metadata
 * @throws Error with user-friendly message on validation or upload failure
 */
export async function uploadDeclaration(
  files: FileUploadState
): Promise<UploadResponse> {
  // Build FormData object with correct field names matching backend API
  const formData = new FormData()

  // Single-file uploads
  if (files.arrival_notice)
    formData.append('arrival_notice', files.arrival_notice)
  if (files.bill_of_lading)
    formData.append('bill_of_lading', files.bill_of_lading)
  if (files.invoice) formData.append('invoice', files.invoice)

  // Multi-file upload for Certificate of Origin
  // Backend expects multiple files with the same key name 'certificate_of_origin'
  if (files.certificate_of_origin && files.certificate_of_origin.length > 0) {
    files.certificate_of_origin.forEach((coFile) => {
      formData.append('certificate_of_origin', coFile)
    })
  }

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
      const errorData: UploadErrorResponse = await response
        .json()
        .catch(() => ({
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
      throw new Error(
        'Upload timeout. Please check your connection and try again.'
      )
    }

    // Handle network errors
    if (error instanceof Error && error.message.includes('fetch')) {
      throw new Error(
        'Network error. Please check your connection and try again.'
      )
    }

    // Re-throw other errors
    throw error
  }
}

/**
 * Get declaration processing status
 * @param id - Declaration UUID
 * @returns Current status and processing progress
 * @throws Error if declaration not found (404) or user not authorized (401/403)
 */
export async function getDeclarationStatus(
  id: string
): Promise<StatusResponse> {
  try {
    return await apiClient<StatusResponse>(`/declarations/${id}/status`, {
      method: 'GET',
    })
  } catch (error) {
    if (error instanceof Error) {
      // Handle 404 - declaration not found
      if (error.message.includes('404')) {
        throw new Error(
          'Declaration not found. Please check the ID and try again.'
        )
      }
      // Handle 401/403 - unauthorized
      if (error.message.includes('401') || error.message.includes('403')) {
        throw new Error('You are not authorized to view this declaration.')
      }
    }
    // Re-throw other errors
    throw error
  }
}

/**
 * Retry processing for a failed declaration
 * @param id - Declaration UUID
 * @returns Confirmation message and declaration ID
 * @throws Error if declaration not found or user not authorized
 */
export async function retryProcessing(
  id: string
): Promise<RetryProcessingResponse> {
  try {
    return await apiClient<RetryProcessingResponse>(
      `/declarations/${id}/process`,
      {
        method: 'POST',
      }
    )
  } catch (error) {
    if (error instanceof Error) {
      // Handle 404 - declaration not found
      if (error.message.includes('404')) {
        throw new Error('Declaration not found. Cannot retry processing.')
      }
      // Handle 401/403 - unauthorized
      if (error.message.includes('401') || error.message.includes('403')) {
        throw new Error('You are not authorized to retry this declaration.')
      }
    }
    // Re-throw other errors
    throw error
  }
}

/**
 * Get PDF file for a declaration document
 * @param declarationId - Declaration UUID
 * @param filename - PDF filename (e.g., AN.pdf, BOL.pdf, CO_1.pdf, INVOICE.pdf)
 * @returns Blob object containing the PDF file data
 * @throws Error if file not found (404) or user not authorized (401/403)
 */
export async function getPDFFile(
  declarationId: string,
  filename: string
): Promise<Blob> {
  const url = `${API_BASE_URL}/declarations/${declarationId}/files/${filename}`

  try {
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include', // Include cookies for JWT authentication
    })

    if (!response.ok) {
      // Handle HTTP errors
      if (response.status === 404) {
        throw new Error(`File "${filename}" not found for this declaration.`)
      }
      if (response.status === 401 || response.status === 403) {
        throw new Error('You are not authorized to access this file.')
      }
      throw new Error(`Failed to fetch PDF file: HTTP ${response.status}`)
    }

    // Return the response body as a Blob
    return response.blob()
  } catch (error) {
    if (error instanceof Error) {
      throw error
    }
    throw new Error('Failed to fetch PDF file. Please try again.')
  }
}

/**
 * Declaration metadata interface for uploaded files
 */
export interface DeclarationMetadata {
  id: string
  uploaded_files: {
    arrival_notice?: string
    bill_of_lading?: string
    certificate_of_origin?: string[] // Array for multiple C/O files
    invoice?: string
  }
}

/**
 * Get declaration metadata to determine available files
 * @param id - Declaration UUID
 * @returns Declaration metadata with uploaded files
 * @throws Error if declaration not found or user not authorized
 */
export async function getDeclarationMetadata(
  id: string
): Promise<DeclarationMetadata> {
  try {
    return await apiClient<DeclarationMetadata>(`/declarations/${id}`, {
      method: 'GET',
    })
  } catch (error) {
    if (error instanceof Error) {
      if (error.message.includes('404')) {
        throw new Error('Declaration not found.')
      }
      if (error.message.includes('401') || error.message.includes('403')) {
        throw new Error('You are not authorized to view this declaration.')
      }
    }
    throw error
  }
}
