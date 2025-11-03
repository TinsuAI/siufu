import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { usePDFDocument } from '@/hooks/use-pdf-document'
import * as api from '@/lib/api'

// Mock the API module
vi.mock('@/lib/api', () => ({
  getPDFFile: vi.fn(),
}))

describe('usePDFDocument', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    // Create a new QueryClient for each test to ensure isolation
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false, // Disable retries for tests
        },
      },
    })
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('should fetch PDF file successfully', async () => {
    // Arrange
    const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' })
    vi.mocked(api.getPDFFile).mockResolvedValue(mockBlob)

    // Act
    const { result } = renderHook(
      () => usePDFDocument('decl-123', 'INVOICE.pdf'),
      { wrapper }
    )

    // Assert - Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for the query to complete
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Assert - Successfully loaded
    expect(result.current.data).toBe(mockBlob)
    expect(api.getPDFFile).toHaveBeenCalledWith('decl-123', 'INVOICE.pdf')
    expect(api.getPDFFile).toHaveBeenCalledTimes(1)
  })

  it('should cache PDF file (subsequent calls use cached data)', async () => {
    // Arrange
    const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' })
    vi.mocked(api.getPDFFile).mockResolvedValue(mockBlob)

    // Act - First call
    const { result: result1 } = renderHook(
      () => usePDFDocument('decl-123', 'AN.pdf'),
      { wrapper }
    )
    await waitFor(() => expect(result1.current.isSuccess).toBe(true))

    // Act - Second call with same params (should use cache)
    const { result: result2 } = renderHook(
      () => usePDFDocument('decl-123', 'AN.pdf'),
      { wrapper }
    )

    // Assert - Second call should immediately return cached data
    await waitFor(() => expect(result2.current.isSuccess).toBe(true))
    expect(result2.current.data).toBe(mockBlob)

    // API should only be called once (cache hit)
    expect(api.getPDFFile).toHaveBeenCalledTimes(1)
  })

  it('should handle 404 error (file not found)', async () => {
    // Arrange
    const error = new Error(
      'File "MISSING.pdf" not found for this declaration.'
    )
    vi.mocked(api.getPDFFile).mockRejectedValue(error)

    // Act
    const { result } = renderHook(
      () => usePDFDocument('decl-123', 'MISSING.pdf'),
      { wrapper }
    )

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toEqual(error)
    expect(api.getPDFFile).toHaveBeenCalledWith('decl-123', 'MISSING.pdf')
  })

  it('should handle 401/403 authentication errors', async () => {
    // Arrange
    const error = new Error('You are not authorized to access this file.')
    vi.mocked(api.getPDFFile).mockRejectedValue(error)

    // Act
    const { result } = renderHook(() => usePDFDocument('decl-456', 'BOL.pdf'), {
      wrapper,
    })

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toEqual(error)
  })

  it('should not fetch if declarationId or filename is empty', () => {
    // Act - Empty declarationId
    const { result: result1 } = renderHook(() => usePDFDocument('', 'AN.pdf'), {
      wrapper,
    })

    // Assert - Query should be disabled
    expect(result1.current.isLoading).toBe(false)
    expect(result1.current.data).toBeUndefined()
    expect(api.getPDFFile).not.toHaveBeenCalled()

    // Act - Empty filename
    const { result: result2 } = renderHook(
      () => usePDFDocument('decl-123', ''),
      { wrapper }
    )

    // Assert - Query should be disabled
    expect(result2.current.isLoading).toBe(false)
    expect(result2.current.data).toBeUndefined()
    expect(api.getPDFFile).not.toHaveBeenCalled()
  })
})
