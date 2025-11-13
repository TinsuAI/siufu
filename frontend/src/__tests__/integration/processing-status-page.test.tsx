/**
 * Integration tests for Processing Status Page
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProcessingStatusPage from '@/app/[locale]/declarations/[id]/page'
import { DeclarationStatus } from '@/types/declaration'
import * as api from '@/lib/api'

// Mock Next.js navigation hooks
const mockPush = vi.fn()
const mockParams = { id: 'test-declaration-id' }

vi.mock('@/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

vi.mock('next/navigation', () => ({
  useParams: () => mockParams,
}))

// Mock the API module
vi.mock('@/lib/api', () => ({
  getDeclarationStatus: vi.fn(),
  retryProcessing: vi.fn(),
}))

describe('ProcessingStatusPage Integration Tests', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
        mutations: {
          retry: false,
        },
      },
    })
    // Clear sessionStorage
    sessionStorage.clear()
  })

  afterEach(() => {
    queryClient.clear()
    vi.clearAllMocks()
    vi.useRealTimers()
    mockPush.mockClear()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('should load and display initial PROCESSING status', async () => {
    const mockStatus = {
      id: 'test-declaration-id',
      status: DeclarationStatus.PROCESSING,
      processing_progress: 0.3,
      processing_error: null,
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)

    render(<ProcessingStatusPage />, { wrapper })

    // Should show loading state initially
    expect(screen.getByText('Loading status...')).toBeInTheDocument()

    // Wait for status to load
    await waitFor(() => {
      expect(screen.getByText(/Processing Declaration/)).toBeInTheDocument()
    })

    // Should display processing stages
    expect(screen.getAllByText('OCR Processing').length).toBeGreaterThan(0)
    expect(screen.getAllByText('AI Extraction').length).toBeGreaterThan(0)

    // Should display progress
    expect(screen.getByText('30%')).toBeInTheDocument()

    // Should display background processing message
    expect(
      screen.getByText(/You can safely close this page/)
    ).toBeInTheDocument()
  })

  it('should update status via polling and show transitions', async () => {
    // First call: PROCESSING
    const mockStatus1 = {
      id: 'test-declaration-id',
      status: DeclarationStatus.PROCESSING,
      processing_progress: 0.3,
      processing_error: null,
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    // Second call: VALIDATING
    const mockStatus2 = {
      ...mockStatus1,
      status: DeclarationStatus.VALIDATING,
      processing_progress: 0.8,
    }

    // Third call: READY_FOR_REVIEW
    const mockStatus3 = {
      ...mockStatus1,
      status: DeclarationStatus.READY_FOR_REVIEW,
      processing_progress: 1.0,
    }

    vi.mocked(api.getDeclarationStatus)
      .mockResolvedValueOnce(mockStatus1)
      .mockResolvedValueOnce(mockStatus2)
      .mockResolvedValueOnce(mockStatus3)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('30%')).toBeInTheDocument()
    })

    // Advance time to trigger first poll (2 seconds)
    await act(async () => {
      await queryClient.refetchQueries({
        queryKey: ['declarations', 'test-declaration-id', 'status'],
      })
    })

    await waitFor(() => {
      expect(screen.getByText('80%')).toBeInTheDocument()
    })

    await act(async () => {
      await queryClient.refetchQueries({
        queryKey: ['declarations', 'test-declaration-id', 'status'],
      })
    })

    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument()
    })
  })

  it('should auto-redirect to review page when READY_FOR_REVIEW', async () => {
    const mockStatus = {
      id: 'test-declaration-id',
      status: DeclarationStatus.READY_FOR_REVIEW,
      processing_progress: 1.0,
      processing_error: null,
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)
    const timeoutSpy = vi.spyOn(global, 'setTimeout')

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for status to load
    await waitFor(() => {
      expect(screen.getByText('Processing Complete!')).toBeInTheDocument()
    })

    // Should show redirect message
    expect(screen.getByText(/Redirecting to review page/)).toBeInTheDocument()

    // Execute redirect callback immediately
    expect(timeoutSpy).toHaveBeenCalled()
    const redirectCall = timeoutSpy.mock.calls.find(
      ([, delay]) => delay === 2000
    )
    expect(redirectCall).toBeDefined()
    const redirectCallback = redirectCall?.[0] as () => void
    await act(async () => {
      redirectCallback()
    })

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        '/declarations/test-declaration-id/review'
      )
    })

    timeoutSpy.mockRestore()
  })

  it('should display error message when status is FAILED', async () => {
    const mockStatus = {
      id: 'test-declaration-id',
      status: DeclarationStatus.FAILED,
      processing_progress: 0.4,
      processing_error: 'OCR extraction failed: Invalid PDF format',
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for status to load
    await waitFor(() => {
      expect(screen.getAllByText('Processing Failed').length).toBeGreaterThan(0)
    })

    // Should display error message
    expect(
      screen.getByText(/OCR extraction failed: Invalid PDF format/)
    ).toBeInTheDocument()

    // Should show retry button
    expect(
      screen.getByRole('button', { name: /Retry Processing/ })
    ).toBeInTheDocument()
  })

  it('should show Retry Processing button and handle retry on FAILED status', async () => {
    const mockStatus = {
      id: 'test-declaration-id',
      status: DeclarationStatus.FAILED,
      processing_progress: 0.2,
      processing_error: 'Network timeout during OCR',
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    const mockRetryResponse = {
      message: 'Processing queued',
      declaration_id: 'test-declaration-id',
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)
    vi.mocked(api.retryProcessing).mockResolvedValue(mockRetryResponse)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getAllByText('Processing Failed').length).toBeGreaterThan(0)
    })

    // Find and click retry button
    const retryButton = screen.getByRole('button', {
      name: /Retry Processing \(0\/3\)/,
    })
    const user = userEvent.setup()
    await user.click(retryButton)

    // Wait for retry to complete
    await waitFor(() => {
      expect(api.retryProcessing).toHaveBeenCalledWith('test-declaration-id')
    })
  })

  it('should show Contact Support after 3 retry attempts', async () => {
    const mockStatus = {
      id: 'test-declaration-id',
      status: DeclarationStatus.FAILED,
      processing_progress: 0.2,
      processing_error: 'Persistent error',
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    const mockRetryResponse = {
      message: 'Processing queued',
      declaration_id: 'test-declaration-id',
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)
    vi.mocked(api.retryProcessing).mockResolvedValue(mockRetryResponse)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getAllByText('Processing Failed').length).toBeGreaterThan(0)
    })

    const user = userEvent.setup()

    // Retry 3 times
    for (let i = 0; i < 3; i++) {
      const retryButton = screen.getByRole('button', {
        name: new RegExp(`Retry Processing \\(${i}/3\\)`),
      })
      await user.click(retryButton)

      await waitFor(() => {
        expect(api.retryProcessing).toHaveBeenCalledTimes(i + 1)
      })
    }

    // After 3 retries, should show Contact Support message
    await waitFor(() => {
      expect(screen.getByText(/Contact Support/)).toBeInTheDocument()
      expect(
        screen.getByText(/Error processing declaration/)
      ).toBeInTheDocument()
    })

    // Retry button should no longer be visible
    expect(
      screen.queryByRole('button', { name: /Retry Processing/ })
    ).not.toBeInTheDocument()
  })

  it('should allow navigation away and continue polling on return', async () => {
    const mockStatus = {
      id: 'test-declaration-id',
      status: DeclarationStatus.PROCESSING,
      processing_progress: 0.5,
      processing_error: null,
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)
    const { unmount } = render(<ProcessingStatusPage />, { wrapper })

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    // Unmount (simulate navigation away)
    unmount()

    // Re-mount (simulate navigation back)
    render(<ProcessingStatusPage />, { wrapper })

    // Wait for status to load again
    await waitFor(() => {
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    // Polling should resume
    await act(async () => {
      await queryClient.refetchQueries({
        queryKey: ['declarations', 'test-declaration-id', 'status'],
      })
    })

    await waitFor(() => {
      expect(api.getDeclarationStatus).toHaveBeenCalled()
    })
  })

  it('should display Upload New Declaration button on FAILED status', async () => {
    const mockStatus = {
      id: 'test-declaration-id',
      status: DeclarationStatus.FAILED,
      processing_progress: 0.3,
      processing_error: 'Processing failed',
      processing_log: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getAllByText('Processing Failed').length).toBeGreaterThan(0)
    })

    // Should show Upload New Declaration button
    const uploadButton = screen.getByRole('button', {
      name: /Upload New Declaration/,
    })
    expect(uploadButton).toBeInTheDocument()

    // Click button
    const user = userEvent.setup()
    await user.click(uploadButton)

    // Should navigate to upload page
    expect(mockPush).toHaveBeenCalledWith('/upload')
  })

  it('should handle API error and display error message', async () => {
    const mockError = new Error('Declaration not found')
    vi.mocked(api.getDeclarationStatus).mockRejectedValue(mockError)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Error Loading Status')).toBeInTheDocument()
    })

    expect(screen.getByText('Declaration not found')).toBeInTheDocument()
  })
})
