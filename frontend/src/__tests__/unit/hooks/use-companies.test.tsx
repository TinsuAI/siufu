/**
 * Unit tests for useCompanies hook
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useCompanies,
  useCompany,
  useCreateCompany,
  useUpdateCompany,
  useDeleteCompany,
  useDuplicates,
  useMergeCompanies,
} from '@/hooks/use-companies'
import * as api from '@/lib/api'
import type { CompanyDetail, CompanyListResponse } from '@/types/company'

// Mock the API module
vi.mock('@/lib/api', () => ({
  getCompanies: vi.fn(),
  getCompany: vi.fn(),
  createCompany: vi.fn(),
  updateCompany: vi.fn(),
  deleteCompany: vi.fn(),
  getDuplicates: vi.fn(),
  mergeCompanies: vi.fn(),
}))

describe('useCompanies hooks', () => {
  let queryClient: QueryClient

  beforeEach(() => {
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

  describe('useCompanies', () => {
    it('should fetch companies list successfully', async () => {
      const mockResponse: CompanyListResponse = {
        companies: [
          {
            id: 'company-1',
            name: 'Test Company',
            type: 'importers',
            declaration_count: 5,
            last_seen: '2024-01-01T00:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        limit: 10,
        total_pages: 1,
      }

      vi.mocked(api.getCompanies).mockResolvedValue(mockResponse)

      const { result } = renderHook(
        () =>
          useCompanies({
            type: 'importers',
            page: 1,
            limit: 10,
          }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(api.getCompanies).toHaveBeenCalledWith({
        type: 'importers',
        page: 1,
        limit: 10,
      })
      expect(result.current.data).toEqual(mockResponse)
    })
  })

  describe('useCompany', () => {
    it('should fetch single company successfully', async () => {
      const mockCompany: CompanyDetail = {
        id: 'company-1',
        name: 'Test Company',
        type: 'importers',
        tax_code: '123456',
        declaration_count: 5,
        last_seen: '2024-01-01T00:00:00Z',
        declarations: [],
      }

      vi.mocked(api.getCompany).mockResolvedValue(mockCompany)

      const { result } = renderHook(
        () => useCompany('company-1', 'importers'),
        {
          wrapper,
        }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(api.getCompany).toHaveBeenCalledWith('company-1', 'importers')
      expect(result.current.data).toEqual(mockCompany)
    })

    it('should not fetch if id is undefined', async () => {
      const { result } = renderHook(() => useCompany(undefined, 'importers'), {
        wrapper,
      })

      expect(result.current.isPending).toBe(true)
      expect(api.getCompany).not.toHaveBeenCalled()
    })
  })

  describe('useCreateCompany', () => {
    it('should create company and invalidate cache', async () => {
      const mockCompany: CompanyDetail = {
        id: 'company-new',
        name: 'New Company',
        type: 'importers',
        tax_code: '789012',
        declaration_count: 0,
        last_seen: '2024-01-01T00:00:00Z',
        declarations: [],
      }

      vi.mocked(api.createCompany).mockResolvedValue(mockCompany)

      const { result } = renderHook(() => useCreateCompany(), { wrapper })

      result.current.mutate({
        type: 'importers',
        data: {
          name: 'New Company',
          tax_code: '789012',
        },
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(api.createCompany).toHaveBeenCalledWith('importers', {
        name: 'New Company',
        tax_code: '789012',
      })
      expect(result.current.data).toEqual(mockCompany)
    })
  })

  describe('useUpdateCompany', () => {
    it('should update company and invalidate cache', async () => {
      const mockCompany: CompanyDetail = {
        id: 'company-1',
        name: 'Updated Company',
        type: 'importers',
        tax_code: '123456',
        declaration_count: 5,
        last_seen: '2024-01-01T00:00:00Z',
        declarations: [],
      }

      vi.mocked(api.updateCompany).mockResolvedValue(mockCompany)

      const { result } = renderHook(() => useUpdateCompany(), { wrapper })

      result.current.mutate({
        id: 'company-1',
        type: 'importers',
        data: {
          name: 'Updated Company',
        },
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(api.updateCompany).toHaveBeenCalledWith('company-1', 'importers', {
        name: 'Updated Company',
      })
      expect(result.current.data).toEqual(mockCompany)
    })
  })

  describe('useDeleteCompany', () => {
    it('should delete company and invalidate cache', async () => {
      vi.mocked(api.deleteCompany).mockResolvedValue()

      const { result } = renderHook(() => useDeleteCompany(), { wrapper })

      result.current.mutate({
        id: 'company-1',
        type: 'importers',
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(api.deleteCompany).toHaveBeenCalledWith('company-1', 'importers')
    })
  })

  describe('useDuplicates', () => {
    it('should fetch duplicate companies', async () => {
      const mockDuplicates = [
        {
          company1: {
            id: 'comp-1',
            name: 'Company A',
            type: 'importers' as const,
          },
          company2: {
            id: 'comp-2',
            name: 'Company A Inc',
            type: 'importers' as const,
          },
          similarity_score: 0.95,
        },
      ]

      vi.mocked(api.getDuplicates).mockResolvedValue(mockDuplicates)

      const { result } = renderHook(() => useDuplicates('importers'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(api.getDuplicates).toHaveBeenCalledWith('importers')
      expect(result.current.data).toEqual(mockDuplicates)
    })
  })

  describe('useMergeCompanies', () => {
    it('should merge companies and invalidate cache', async () => {
      const mockMergedCompany: CompanyDetail = {
        id: 'company-1',
        name: 'Merged Company',
        type: 'importers',
        tax_code: '123456',
        declaration_count: 10,
        last_seen: '2024-01-01T00:00:00Z',
        declarations: [],
      }

      vi.mocked(api.mergeCompanies).mockResolvedValue(mockMergedCompany)

      const { result } = renderHook(() => useMergeCompanies(), { wrapper })

      result.current.mutate({
        type: 'importers',
        keepId: 'company-1',
        mergeId: 'company-2',
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(api.mergeCompanies).toHaveBeenCalledWith(
        'importers',
        'company-1',
        'company-2'
      )
      expect(result.current.data).toEqual(mockMergedCompany)
    })
  })
})
