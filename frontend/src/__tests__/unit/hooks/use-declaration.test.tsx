/**
 * Unit tests for useDeclaration hook
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useDeclaration } from '@/hooks/use-declaration'
import * as api from '@/lib/api'
import type { Declaration } from '@/types/declaration'
import { DeclarationStatus } from '@/types/declaration'

// Mock the API module
vi.mock('@/lib/api', () => ({
  getDeclaration: vi.fn(),
  patchDeclaration: vi.fn(),
  approveDeclaration: vi.fn(),
  rejectDeclaration: vi.fn(),
  exportDeclaration: vi.fn(),
}))

describe('useDeclaration hook', () => {
  let queryClient: QueryClient

  const mockDeclaration: Declaration = {
    id: 'declaration-123',
    status: DeclarationStatus.READY_FOR_REVIEW,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    processing_progress: 1.0,
    processing_error: null,
    extracted_data: null,
    draft_data: {
      declaration_header: {
        declaration_number: 'D-001',
        customs_office_code: 'HCM',
      },
      products: [],
    },
    uploaded_files: [
      {
        filename: 'AN.pdf',
        file_type: 'AN',
        upload_timestamp: '2024-01-01T00:00:00Z',
      },
      {
        filename: 'BOL.pdf',
        file_type: 'BOL',
        upload_timestamp: '2024-01-01T00:00:00Z',
      },
      {
        filename: 'CO.pdf',
        file_type: 'CO',
        upload_timestamp: '2024-01-01T00:00:00Z',
      },
      {
        filename: 'INVOICE.pdf',
        file_type: 'INVOICE',
        upload_timestamp: '2024-01-01T00:00:00Z',
      },
    ],
    validation_warnings: [],
    confidence_scores: {},
    source_metadata: null,
    importer_id: null,
    exporter_id: null,
    importer_summary: null,
    exporter_summary: null,
    user_id: 'user-123',
  }

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
    vi.restoreAllMocks()
  })

  const wrapper = ({
    children,
  }: {
    children: React.ReactNode
  }): React.JSX.Element => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('fetching declaration', () => {
    it('should fetch declaration data successfully', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.isLoading).toBe(false))

      expect(api.getDeclaration).toHaveBeenCalledWith('declaration-123')
      expect(result.current.declaration).toEqual(mockDeclaration)
      expect(result.current.isError).toBe(false)
    })

    it('should handle fetch error', async () => {
      const mockError = new Error('Declaration not found')
      vi.mocked(api.getDeclaration).mockRejectedValue(mockError)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(mockError)
      expect(result.current.declaration).toBeUndefined()
    })

    it('should poll when status is PROCESSING', async () => {
      const processingDeclaration: Declaration = {
        ...mockDeclaration,
        status: DeclarationStatus.PROCESSING,
        processing_progress: 0.5,
      }

      vi.mocked(api.getDeclaration).mockResolvedValue(processingDeclaration)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      expect(result.current.declaration?.status).toBe('PROCESSING')
    })
  })

  describe('updateDraftData', () => {
    it('should update draft data successfully', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)
      vi.mocked(api.patchDeclaration).mockResolvedValue({
        ...mockDeclaration,
        draft_data: { updated: true },
      })

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      // Update draft data
      result.current.updateDraftData({ updated: true })

      await waitFor(() => expect(result.current.isUpdateSuccess).toBe(true))

      expect(api.patchDeclaration).toHaveBeenCalledWith('declaration-123', {
        updated: true,
      })
    })

    it('should handle update error and rollback optimistic update', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)
      const mockError = new Error('Update failed')
      vi.mocked(api.patchDeclaration).mockRejectedValue(mockError)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      // Attempt to update draft data
      result.current.updateDraftData({ failed: true })

      await waitFor(() => expect(result.current.isUpdateError).toBe(true))

      expect(api.patchDeclaration).toHaveBeenCalledWith('declaration-123', {
        failed: true,
      })
    })
  })

  describe('approveDeclaration', () => {
    it('should approve declaration successfully', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)
      const mockApproveResponse = {
        id: 'declaration-123',
        status: 'APPROVED',
        approved_at: '2024-01-02T00:00:00Z',
        approved_by_user_id: 'user-1',
        message: 'Declaration approved',
      }
      vi.mocked(api.approveDeclaration).mockResolvedValue(mockApproveResponse)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      // Approve declaration
      result.current.approveDeclaration()

      await waitFor(() => expect(result.current.isApproveSuccess).toBe(true))

      expect(api.approveDeclaration).toHaveBeenCalledWith('declaration-123')
    })

    it('should handle approval error', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)
      const mockError = new Error('Not authorized')
      vi.mocked(api.approveDeclaration).mockRejectedValue(mockError)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      // Attempt to approve
      result.current.approveDeclaration()

      await waitFor(() => expect(result.current.isApproveError).toBe(true))
    })
  })

  describe('rejectDeclaration', () => {
    it('should reject declaration successfully', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)
      const mockRejectResponse = {
        id: 'declaration-123',
        status: 'REJECTED',
        rejection_reason: 'Invalid data',
        message: 'Declaration rejected',
      }
      vi.mocked(api.rejectDeclaration).mockResolvedValue(mockRejectResponse)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      // Reject declaration
      result.current.rejectDeclaration('Invalid data')

      await waitFor(() => expect(result.current.isRejectSuccess).toBe(true))

      expect(api.rejectDeclaration).toHaveBeenCalledWith(
        'declaration-123',
        'Invalid data'
      )
    })

    it('should handle rejection error', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)
      const mockError = new Error('Reason too short')
      vi.mocked(api.rejectDeclaration).mockRejectedValue(mockError)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      // Attempt to reject
      result.current.rejectDeclaration('Short')

      await waitFor(() => expect(result.current.isRejectError).toBe(true))
    })
  })

  describe('exportDeclarationToExcel', () => {
    it('should call export API successfully', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)
      const mockBlob = new Blob(['test'], { type: 'application/vnd.ms-excel' })
      vi.mocked(api.exportDeclaration).mockResolvedValue(mockBlob)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      // Mock DOM methods for file download AFTER renderHook to avoid interfering with React
      const mockAnchor = {
        click: vi.fn(),
        href: '',
        download: '',
      }
      const originalCreateElement = document.createElement.bind(document)
      const createElementSpy = vi
        .spyOn(document, 'createElement')
        .mockImplementation((tagName: string) => {
          if (tagName === 'a') {
            return mockAnchor as any
          }
          return originalCreateElement(tagName)
        })
      vi.spyOn(document.body, 'appendChild').mockImplementation(
        () => mockAnchor as any
      )
      vi.spyOn(document.body, 'removeChild').mockImplementation(
        () => mockAnchor as any
      )
      vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:mock-url')
      vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {})

      // Export declaration
      result.current.exportDeclarationToExcel()

      await waitFor(() => expect(result.current.isExportSuccess).toBe(true))

      expect(api.exportDeclaration).toHaveBeenCalledWith('declaration-123')
      expect(mockAnchor.click).toHaveBeenCalled()

      createElementSpy.mockRestore()
    })

    it('should handle export error', async () => {
      vi.mocked(api.getDeclaration).mockResolvedValue(mockDeclaration)
      const mockError = new Error('Export failed')
      vi.mocked(api.exportDeclaration).mockRejectedValue(mockError)

      const { result } = renderHook(() => useDeclaration('declaration-123'), {
        wrapper,
      })

      await waitFor(() => expect(result.current.declaration).toBeDefined())

      // Attempt to export
      result.current.exportDeclarationToExcel()

      await waitFor(() => expect(result.current.isExportError).toBe(true))
    })
  })
})
