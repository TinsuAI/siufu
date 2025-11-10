/**
 * Component tests for Declarations List Page
 * Story 3.9: Declaration History List
 *
 * P0 Tests (QA Gate Required):
 * 1. Empty state renders "No declarations found"
 * 2. Table renders with mock data
 * 3. Delete button shows confirmation dialog
 * 4. Search input triggers debounced API call (500ms)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test-utils'
import DeclarationsListPage from '@/app/[locale]/declarations/page'
import * as api from '@/lib/api'

// Mock the API client
vi.mock('@/lib/api', () => ({
  getDeclarations: vi.fn(),
  deleteDeclaration: vi.fn(),
}))

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn(),
  }),
  usePathname: () => '/declarations',
}))

describe('Declarations List Page - P0 Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('P0-1: renders empty state when no declarations exist', async () => {
    // Mock API to return empty list
    vi.mocked(api.getDeclarations).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      total_pages: 0,
    })

    renderWithProviders(<DeclarationsListPage />)

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
    })

    // Verify empty state message is displayed
    expect(screen.getByText(/no declarations found/i)).toBeInTheDocument()

    // Verify the empty state provides helpful guidance
    expect(
      screen.getByText(/upload your first declaration/i)
    ).toBeInTheDocument()
  })

  it('P0-2: renders table with mock declaration data', async () => {
    // Mock API to return list with 2 declarations
    vi.mocked(api.getDeclarations).mockResolvedValue({
      items: [
        {
          id: 'dec-001',
          status: 'APPROVED' as const,
          created_at: '2024-11-01T10:00:00Z',
          updated_at: '2024-11-01T12:00:00Z',
          approved_at: '2024-11-01T12:00:00Z',
          products_count: 5,
        },
        {
          id: 'dec-002',
          status: 'READY_FOR_REVIEW' as const,
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
    })

    renderWithProviders(<DeclarationsListPage />)

    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
    })

    // Verify table headers are present (use getAllByText for "status" since it appears in filter too)
    expect(screen.getByText(/declaration id/i)).toBeInTheDocument()
    expect(screen.getByText(/upload date/i)).toBeInTheDocument()
    const statusHeaders = screen.getAllByText(/status/i)
    expect(statusHeaders.length).toBeGreaterThan(0) // Status appears in filter and table header
    expect(screen.getByText(/products count/i)).toBeInTheDocument()
    expect(screen.getByText(/actions/i)).toBeInTheDocument()

    // Verify declaration IDs are displayed
    expect(screen.getByText('dec-001')).toBeInTheDocument()
    expect(screen.getByText('dec-002')).toBeInTheDocument()

    // Verify products counts are displayed
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()

    // Verify pagination info is displayed
    expect(screen.getByText(/showing 1-2 of 2/i)).toBeInTheDocument()
  })

  it('P0-3: delete button shows confirmation dialog', async () => {
    // Mock API to return list with 1 declaration
    vi.mocked(api.getDeclarations).mockResolvedValue({
      items: [
        {
          id: 'dec-001',
          status: 'APPROVED' as const,
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
    })

    const user = userEvent.setup()
    renderWithProviders(<DeclarationsListPage />)

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('dec-001')).toBeInTheDocument()
    })

    // Find and click delete button (Trash2 icon button)
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    expect(deleteButtons.length).toBeGreaterThan(0)

    await user.click(deleteButtons[0])

    // Verify confirmation dialog appears
    await waitFor(() => {
      expect(
        screen.getByText(/are you sure you want to delete this declaration/i)
      ).toBeInTheDocument()
    })

    // Verify dialog has Cancel and Delete buttons
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    // Delete button exists (there will be multiple "delete" buttons - one in table, one in dialog)
    const allDeleteButtons = screen.getAllByRole('button', { name: /delete/i })
    expect(allDeleteButtons.length).toBeGreaterThan(1) // At least one in table + one in dialog
  })

  it('P0-4: search input triggers debounced API call (500ms)', async () => {
    // Mock API initial response
    vi.mocked(api.getDeclarations).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      total_pages: 0,
    })

    const user = userEvent.setup()
    renderWithProviders(<DeclarationsListPage />)

    // Wait for initial load
    await waitFor(() => {
      expect(api.getDeclarations).toHaveBeenCalledTimes(1)
    })

    // Find search input
    const searchInput = screen.getByPlaceholderText(/search by declaration id/i)
    expect(searchInput).toBeInTheDocument()

    // Type search query quickly (should be debounced)
    await user.type(searchInput, 'dec-001')

    // Immediately after typing, API should not be called again yet
    // (still only the initial call)
    expect(api.getDeclarations).toHaveBeenCalledTimes(1)

    // Wait for debounce delay (500ms)
    await waitFor(
      () => {
        // After debounce, API should be called with search param
        expect(api.getDeclarations).toHaveBeenCalledWith(
          expect.objectContaining({
            search: 'dec-001',
          })
        )
      },
      { timeout: 1000 }
    )

    // Verify total calls: initial + debounced search
    expect(api.getDeclarations).toHaveBeenCalledTimes(2)
  })

  it('P0-5: displays error state when API fails', async () => {
    // Mock API to return error
    vi.mocked(api.getDeclarations).mockRejectedValue(
      new Error('Failed to fetch declarations')
    )

    renderWithProviders(<DeclarationsListPage />)

    // Wait for error state to appear
    await waitFor(() => {
      expect(
        screen.getByText(/error loading declarations/i)
      ).toBeInTheDocument()
    })

    // Verify error message is displayed
    expect(
      screen.getByText(/failed to fetch declarations/i)
    ).toBeInTheDocument()
  })

  it('P0-6: displays loading state while fetching data', async () => {
    // Mock API with delayed response to capture loading state
    vi.mocked(api.getDeclarations).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              items: [],
              total: 0,
              page: 1,
              limit: 20,
              total_pages: 0,
            })
          }, 100)
        })
    )

    renderWithProviders(<DeclarationsListPage />)

    // Verify loading state is displayed initially
    expect(
      screen.getByText(/loading declarations|loading/i)
    ).toBeInTheDocument()

    // Wait for loading to complete
    await waitFor(() => {
      expect(
        screen.queryByText(/loading declarations|loading/i)
      ).not.toBeInTheDocument()
    })
  })
})
