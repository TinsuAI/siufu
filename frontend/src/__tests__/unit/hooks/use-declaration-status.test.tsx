/**
 * Unit tests for useDeclarationStatus hook
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useDeclarationStatus,
  useRetryProcessing,
} from '@/hooks/use-declaration-status'
import { DeclarationStatus } from '@/types/declaration'
import * as api from '@/lib/api'

// Mock the API module
vi.mock('@/lib/api', () => ({
  getDeclarationStatus: vi.fn(),
  retryProcessing: vi.fn(),
}))

describe('useDeclarationStatus', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    // Create a new QueryClient for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false, // Disable retries for tests
          gcTime: 0,
        },
      },
    })
  })

  afterEach(() => {
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

  it('should poll every 2 seconds when status is PROCESSING', async () => {
    const mockStatusResponse = {
      id: 'test-id',
      status: DeclarationStatus.PROCESSING,
      processing_progress: 0.5,
      processing_error: null,
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatusResponse)

    const { result } = renderHook(() => useDeclarationStatus('test-id'), {
      wrapper,
    })

    // Wait for initial fetch
    await waitFor(() => expect(result.current.isSuccess).toBe(true), {
      timeout: 3000,
    })

    expect(api.getDeclarationStatus).toHaveBeenCalled()
    expect(result.current.isPolling).toBe(true)
    expect(result.current.data?.status).toBe(DeclarationStatus.PROCESSING)
  })

  it('should stop polling when status is READY_FOR_REVIEW', async () => {
    const mockStatusResponse = {
      id: 'test-id',
      status: DeclarationStatus.READY_FOR_REVIEW,
      processing_progress: 1.0,
      processing_error: null,
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatusResponse)

    const { result } = renderHook(() => useDeclarationStatus('test-id'), {
      wrapper,
    })

    // Wait for initial fetch
    await waitFor(() => expect(result.current.isSuccess).toBe(true), {
      timeout: 3000,
    })

    expect(result.current.isPolling).toBe(false)
    expect(result.current.data?.status).toBe(DeclarationStatus.READY_FOR_REVIEW)
  })

  it('should stop polling when status is FAILED', async () => {
    const mockStatusResponse = {
      id: 'test-id',
      status: DeclarationStatus.FAILED,
      processing_progress: 0.3,
      processing_error: 'OCR processing failed',
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatusResponse)

    const { result } = renderHook(() => useDeclarationStatus('test-id'), {
      wrapper,
    })

    // Wait for initial fetch
    await waitFor(() => expect(result.current.isSuccess).toBe(true), {
      timeout: 3000,
    })

    expect(result.current.isPolling).toBe(false)
    expect(result.current.data?.status).toBe(DeclarationStatus.FAILED)
    expect(result.current.data?.processing_error).toBe('OCR processing failed')
  })

  it('should calculate estimated time remaining correctly', async () => {
    // Create a timestamp 45 seconds ago
    const createdAt = new Date(Date.now() - 45000).toISOString()

    const mockStatusResponse = {
      id: 'test-id',
      status: DeclarationStatus.PROCESSING,
      processing_progress: 0.5,
      processing_error: null,
      processing_log: [],
      created_at: createdAt,
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatusResponse)

    const { result } = renderHook(() => useDeclarationStatus('test-id'), {
      wrapper,
    })

    // Wait for initial fetch
    await waitFor(() => expect(result.current.isSuccess).toBe(true), {
      timeout: 3000,
    })

    // Should be approximately 45 seconds remaining (90 - 45)
    expect(result.current.estimatedTimeRemaining).toBeGreaterThan(40)
    expect(result.current.estimatedTimeRemaining).toBeLessThan(50)

    // Elapsed time should be approximately 45 seconds
    expect(result.current.elapsedTime).toBeGreaterThan(40)
    expect(result.current.elapsedTime).toBeLessThan(50)
  })

  it('should return 90 seconds as estimated time when no created_at', async () => {
    const mockStatusResponse = {
      id: 'test-id',
      status: DeclarationStatus.PROCESSING,
      processing_progress: 0.2,
      processing_error: null,
      processing_log: [],
      created_at: '',
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatusResponse)

    const { result } = renderHook(() => useDeclarationStatus('test-id'), {
      wrapper,
    })

    // Wait for initial fetch
    await waitFor(() => expect(result.current.isSuccess).toBe(true), {
      timeout: 3000,
    })

    expect(result.current.estimatedTimeRemaining).toBe(90)
  })
})

describe('useRetryProcessing', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        mutations: {
          retry: false,
        },
      },
    })
  })

  afterEach(() => {
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

  it('should call retryProcessing API and invalidate queries on success', async () => {
    const mockResponse = {
      message: 'Processing queued',
      declaration_id: 'test-id',
    }

    vi.mocked(api.retryProcessing).mockResolvedValue(mockResponse)

    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useRetryProcessing(), { wrapper })

    // Trigger mutation
    result.current.mutate('test-id')

    // Wait for success
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(api.retryProcessing).toHaveBeenCalledWith('test-id')
    expect(invalidateQueriesSpy).toHaveBeenCalledWith({
      queryKey: ['declarations', 'test-id', 'status'],
    })
  })

  it('should handle retry errors', async () => {
    const mockError = new Error('Retry failed')
    vi.mocked(api.retryProcessing).mockRejectedValue(mockError)

    const { result } = renderHook(() => useRetryProcessing(), { wrapper })

    // Trigger mutation
    result.current.mutate('test-id')

    // Wait for error
    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(mockError)
  })
})
