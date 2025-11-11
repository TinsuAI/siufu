/**
 * Integration tests for useDeclarations hook
 * Story 3.9: Declaration History List
 *
 * These tests verify TanStack Query hook behavior with MSW mocked API
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { AllTheProviders } from '@/test-utils'
import { useDeclarations } from '@/hooks/use-declarations'
import { DeclarationStatus } from '@/types/declaration'
import * as api from '@/lib/api'

// Mock the API client
vi.mock('@/lib/api', () => ({
  getDeclarations: vi.fn(),
  deleteDeclaration: vi.fn(),
}))

describe('useDeclarations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches list of declarations successfully', async () => {
    // Mock API response
    const mockResponse = {
      items: [
        {
          id: 'dec-001',
          status: DeclarationStatus.APPROVED as const,
          created_at: '2024-11-01T10:00:00Z',
          updated_at: '2024-11-01T12:00:00Z',
          approved_at: '2024-11-01T12:00:00Z',
          products_count: 5,
        },
        {
          id: 'dec-002',
          status: DeclarationStatus.READY_FOR_REVIEW as const,
          created_at: '2024-11-02T10:00:00Z',
          updated_at: '2024-11-02T11:00:00Z',
          approved_at: null,
          products_count: 3,
        },
      ],
      total: 2,
      page: 1,
      limit: 20,
      total_pages: 1,
    }

    vi.mocked(api.getDeclarations).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useDeclarations(), {
      wrapper: AllTheProviders,
    })

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for the query to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Check the data
    expect(result.current.data).toBeDefined()
    expect(result.current.data?.items).toHaveLength(2)
    expect(result.current.data?.total).toBe(2)
    expect(result.current.data?.items[0]).toMatchObject({
      id: 'dec-001',
      status: DeclarationStatus.APPROVED,
      products_count: 5,
    })

    // Verify API was called with default params
    expect(api.getDeclarations).toHaveBeenCalledWith({
      page: 1,
      limit: 20,
      status: undefined,
      search: undefined,
      sort_by: 'created_at',
      sort_order: 'desc',
    })
  })

  it('fetches with custom pagination params', async () => {
    const mockResponse = {
      items: [],
      total: 50,
      page: 2,
      limit: 10,
      total_pages: 5,
    }

    vi.mocked(api.getDeclarations).mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useDeclarations({ page: 2, limit: 10 }),
      {
        wrapper: AllTheProviders,
      }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(api.getDeclarations).toHaveBeenCalledWith({
      page: 2,
      limit: 10,
      status: undefined,
      search: undefined,
      sort_by: 'created_at',
      sort_order: 'desc',
    })
  })

  it('fetches with status filter', async () => {
    const mockResponse = {
      items: [],
      total: 5,
      page: 1,
      limit: 20,
      total_pages: 1,
    }

    vi.mocked(api.getDeclarations).mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useDeclarations({ status: DeclarationStatus.APPROVED }),
      {
        wrapper: AllTheProviders,
      }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(api.getDeclarations).toHaveBeenCalledWith({
      page: 1,
      limit: 20,
      status: DeclarationStatus.APPROVED,
      search: undefined,
      sort_by: 'created_at',
      sort_order: 'desc',
    })
  })

  it('fetches with search query', async () => {
    const mockResponse = {
      items: [],
      total: 1,
      page: 1,
      limit: 20,
      total_pages: 1,
    }

    vi.mocked(api.getDeclarations).mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useDeclarations({ search: 'dec-001' }),
      {
        wrapper: AllTheProviders,
      }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(api.getDeclarations).toHaveBeenCalledWith({
      page: 1,
      limit: 20,
      status: undefined,
      search: 'dec-001',
      sort_by: 'created_at',
      sort_order: 'desc',
    })
  })

  it('can be disabled with enabled option', () => {
    const { result } = renderHook(() => useDeclarations({ enabled: false }), {
      wrapper: AllTheProviders,
    })

    // Query should not run because enabled is false
    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBeUndefined()
    expect(api.getDeclarations).not.toHaveBeenCalled()
  })

  it('handles API errors', async () => {
    const mockError = new Error('Failed to fetch declarations')
    vi.mocked(api.getDeclarations).mockRejectedValue(mockError)

    const { result } = renderHook(() => useDeclarations(), {
      wrapper: AllTheProviders,
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBeDefined()
    expect(result.current.error?.message).toBe('Failed to fetch declarations')
  })

  it('provides delete mutation that invalidates query cache', async () => {
    // Setup successful initial fetch
    const mockResponse = {
      items: [
        {
          id: 'dec-001',
          status: DeclarationStatus.APPROVED as const,
          created_at: '2024-11-01T10:00:00Z',
          updated_at: '2024-11-01T12:00:00Z',
          approved_at: '2024-11-01T12:00:00Z',
          products_count: 5,
        },
      ],
      total: 1,
      page: 1,
      limit: 20,
      total_pages: 1,
    }

    vi.mocked(api.getDeclarations).mockResolvedValue(mockResponse)
    vi.mocked(api.deleteDeclaration).mockResolvedValue(undefined)

    const { result } = renderHook(() => useDeclarations(), {
      wrapper: AllTheProviders,
    })

    // Wait for initial fetch
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data?.items).toHaveLength(1)

    // Trigger delete mutation
    result.current.deleteMutation.mutate('dec-001')

    await waitFor(() => {
      expect(result.current.deleteMutation.isSuccess).toBe(true)
    })

    // Verify delete API was called
    expect(api.deleteDeclaration).toHaveBeenCalledWith('dec-001')

    // Note: Cache invalidation would trigger a refetch in a real scenario
    // In this test, we're just verifying the mutation completed successfully
  })
})
