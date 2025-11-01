/**
 * Integration tests for Processing Status Page
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProcessingStatusPage from '@/app/declarations/[id]/page'
import { DeclarationStatus } from '@/types/declaration'
import * as api from '@/lib/api'

// Mock Next.js navigation hooks
const mockPush = vi.fn()
const mockParams = { id: 'test-declaration-id' }

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useParams: () => mockParams,
}))

// Mock the API module
vi.mock('@/lib/api', () => ({
  getDeclarationStatus: vi.fn(),
  retryProcessing: vi.fn(),
}))

describe('ProcessingStatusPage Integration Tests', () => {
  let queryClient: QueryClient
  let user: ReturnType<typeof userEvent.setup>

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
    user = userEvent.setup()
    vi.useFakeTimers()
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
    expect(screen.getByText('OCR Processing')).toBeInTheDocument()
    expect(screen.getByText('AI Extraction')).toBeInTheDocument()

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
    vi.advanceTimersByTime(2000)

    // Wait for status update to VALIDATING
    await waitFor(() => {
      expect(screen.getByText('80%')).toBeInTheDocument()
    })

    // Advance time to trigger second poll
    vi.advanceTimersByTime(2000)

    // Wait for status update to READY_FOR_REVIEW
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
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for status to load
    await waitFor(() => {
      expect(screen.getByText('Processing Complete!')).toBeInTheDocument()
    })

    // Should show redirect message
    expect(screen.getByText(/Redirecting to review page/)).toBeInTheDocument()

    // Advance time by 2 seconds to trigger redirect
    vi.advanceTimersByTime(2000)

    // Wait for redirect
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        '/declarations/test-declaration-id/review'
      )
    })
  })

  it('should display error message when status is FAILED', async () => {
    const mockStatus = {
      id: 'test-declaration-id',
      status: DeclarationStatus.FAILED,
      processing_progress: 0.4,
      processing_error: 'OCR extraction failed: Invalid PDF format',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for status to load
    await waitFor(() => {
      expect(screen.getByText('Processing Failed')).toBeInTheDocument()
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
      expect(screen.getByText('Processing Failed')).toBeInTheDocument()
    })

    // Find and click retry button
    const retryButton = screen.getByRole('button', {
      name: /Retry Processing \(0\/3\)/,
    })
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
      expect(screen.getByText('Processing Failed')).toBeInTheDocument()
    })

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
    vi.advanceTimersByTime(2000)

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
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    vi.mocked(api.getDeclarationStatus).mockResolvedValue(mockStatus)

    render(<ProcessingStatusPage />, { wrapper })

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByText('Processing Failed')).toBeInTheDocument()
    })

    // Should show Upload New Declaration button
    const uploadButton = screen.getByRole('button', {
      name: /Upload New Declaration/,
    })
    expect(uploadButton).toBeInTheDocument()

    // Click button
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
