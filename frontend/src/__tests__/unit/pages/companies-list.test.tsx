/**
 * Unit tests for Companies List Page
 * Tests rendering, search, filter, pagination, and delete functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CompaniesPage from '@/app/[locale]/companies/page'
import * as api from '@/lib/api'
import type {
  CompanyListResponse,
  ImporterListItem,
  ExporterListItem,
} from '@/types/company'

// Mock Next.js router
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// Mock API functions
vi.mock('@/lib/api', () => ({
  getCompanies: vi.fn(),
  deleteCompany: vi.fn(),
}))

// Mock confirm dialog
const originalConfirm = global.confirm
beforeEach(() => {
  global.confirm = vi.fn()
  mockPush.mockClear()
})

afterEach(() => {
  global.confirm = originalConfirm
  vi.clearAllMocks()
})

// Test data
const mockImporters: ImporterListItem[] = [
  {
    id: 'importer-1',
    tax_code: '1234567890',
    name: 'Test Importer A',
    declaration_count: 10,
    is_verified: true,
    updated_at: '2025-01-15T10:00:00Z',
    created_at: '2025-01-01T10:00:00Z',
  },
  {
    id: 'importer-2',
    tax_code: '0987654321',
    name: 'Test Importer B',
    declaration_count: 5,
    is_verified: false,
    updated_at: '2025-01-14T10:00:00Z',
    created_at: '2025-01-02T10:00:00Z',
  },
]

const mockExporters: ExporterListItem[] = [
  {
    id: 'exporter-1',
    name: 'Test Exporter A',
    country_code: 'CN',
    declaration_count: 20,
    is_verified: true,
    updated_at: '2025-01-15T10:00:00Z',
    created_at: '2025-01-01T10:00:00Z',
  },
  {
    id: 'exporter-2',
    name: 'Test Exporter B',
    country_code: 'US',
    declaration_count: 8,
    is_verified: false,
    updated_at: '2025-01-14T10:00:00Z',
    created_at: '2025-01-02T10:00:00Z',
  },
]

const mockImportersResponse: CompanyListResponse = {
  items: mockImporters,
  total: 2,
  page: 1,
  limit: 20,
  total_pages: 1,
}

const mockExportersResponse: CompanyListResponse = {
  items: mockExporters,
  total: 2,
  page: 1,
  limit: 20,
  total_pages: 1,
}

const mockEmptyResponse: CompanyListResponse = {
  items: [],
  total: 0,
  page: 1,
  limit: 20,
  total_pages: 0,
}

// Helper to render with QueryClient
function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe('CompaniesPage', () => {
  describe('Initial Render', () => {
    it('renders the page title and description', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      expect(screen.getByText('Companies')).toBeInTheDocument()
      expect(
        screen.getByText('Manage importer and exporter master data')
      ).toBeInTheDocument()
    })

    it('renders "Add Company" button', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      const addButton = screen.getByRole('button', { name: /add company/i })
      expect(addButton).toBeInTheDocument()
    })

    it('renders tabs for Importers and Exporters', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      expect(
        screen.getByRole('tab', { name: /importers/i })
      ).toBeInTheDocument()
      expect(
        screen.getByRole('tab', { name: /exporters/i })
      ).toBeInTheDocument()
    })

    it('renders search input with correct placeholder for importers', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      const searchInput = screen.getByPlaceholderText(
        /search by name or tax code/i
      )
      expect(searchInput).toBeInTheDocument()
    })

    it('renders filter and sort controls', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      // Filter dropdown should be present (All Companies, Verified Only, Unverified Only)
      expect(screen.getByText('All Companies')).toBeInTheDocument()
    })

    it('loads importers on initial render', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(api.getCompanies).toHaveBeenCalledWith({
          type: 'importers',
          search: undefined,
          filter: 'all',
          page: 1,
          limit: 20,
          sort_by: 'updated_at',
          sort_order: 'desc',
        })
      })
    })
  })

  describe('Company Cards Display', () => {
    it('renders company cards with correct data for importers', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
        expect(screen.getByText('Test Importer B')).toBeInTheDocument()
      })

      // Check tax code display
      expect(screen.getByText('Tax Code: 1234567890')).toBeInTheDocument()
      expect(screen.getByText('Tax Code: 0987654321')).toBeInTheDocument()

      // Check declaration counts
      expect(screen.getByText('10 declarations')).toBeInTheDocument()
      expect(screen.getByText('5 declarations')).toBeInTheDocument()
    })

    it('displays verified badge for verified companies', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Verified')).toBeInTheDocument()
      })
    })

    it('displays unverified badge for unverified companies', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Unverified')).toBeInTheDocument()
      })
    })

    it('renders View Details and Delete buttons for each company', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        const viewButtons = screen.getAllByRole('button', {
          name: /view details/i,
        })
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i })

        expect(viewButtons).toHaveLength(2)
        expect(deleteButtons).toHaveLength(2)
      })
    })

    it('renders exporter cards with country code instead of tax code', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockExportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      // Switch to exporters tab
      const user = userEvent.setup()
      await user.click(screen.getByRole('tab', { name: /exporters/i }))

      await waitFor(() => {
        expect(screen.getByText('Test Exporter A')).toBeInTheDocument()
      })

      // Check country code display instead of tax code
      expect(screen.getByText('Country: CN')).toBeInTheDocument()
      expect(screen.getByText('Country: US')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('renders empty state when no companies found', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockEmptyResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(
          screen.getByText(
            /no companies found. companies will appear here after processing declarations/i
          )
        ).toBeInTheDocument()
      })
    })
  })

  describe('Loading State', () => {
    it('displays loading message while fetching companies', async () => {
      vi.mocked(api.getCompanies).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockImportersResponse), 100)
          )
      )

      renderWithQueryClient(<CompaniesPage />)

      expect(screen.getByText('Loading companies...')).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })
    })
  })

  describe('Error State', () => {
    it('displays error message when API call fails', async () => {
      vi.mocked(api.getCompanies).mockRejectedValue(new Error('Network error'))

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(
          screen.getByText(/error loading companies: network error/i)
        ).toBeInTheDocument()
      })
    })
  })

  describe('Tab Switching', () => {
    it('switches from importers to exporters tab', async () => {
      vi.mocked(api.getCompanies)
        .mockResolvedValueOnce(mockImportersResponse)
        .mockResolvedValueOnce(mockExportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })

      const user = userEvent.setup()
      await user.click(screen.getByRole('tab', { name: /exporters/i }))

      await waitFor(() => {
        expect(api.getCompanies).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'exporters' })
        )
      })
    })

    it('resets page to 1 when switching tabs', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })

      const user = userEvent.setup()
      await user.click(screen.getByRole('tab', { name: /exporters/i }))

      await waitFor(() => {
        expect(api.getCompanies).toHaveBeenLastCalledWith(
          expect.objectContaining({ page: 1 })
        )
      })
    })

    it('changes search placeholder when switching to exporters', async () => {
      vi.mocked(api.getCompanies)
        .mockResolvedValueOnce(mockImportersResponse)
        .mockResolvedValueOnce(mockExportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      expect(
        screen.getByPlaceholderText(/search by name or tax code/i)
      ).toBeInTheDocument()

      const user = userEvent.setup()
      await user.click(screen.getByRole('tab', { name: /exporters/i }))

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText(/search by name.../i)
        ).toBeInTheDocument()
      })
    })
  })

  describe('Search Functionality', () => {
    it('triggers debounced search after typing', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      const user = userEvent.setup()
      const searchInput = screen.getByPlaceholderText(
        /search by name or tax code/i
      )

      await user.type(searchInput, 'Test Company')

      // Should trigger API call after 500ms debounce
      await waitFor(
        () => {
          expect(api.getCompanies).toHaveBeenCalledWith(
            expect.objectContaining({ search: 'Test Company' })
          )
        },
        { timeout: 1000 }
      )
    })

    it('resets page to 1 when searching', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      const user = userEvent.setup()
      const searchInput = screen.getByPlaceholderText(
        /search by name or tax code/i
      )

      await user.type(searchInput, 'Test')

      await waitFor(
        () => {
          expect(api.getCompanies).toHaveBeenLastCalledWith(
            expect.objectContaining({ page: 1, search: 'Test' })
          )
        },
        { timeout: 1000 }
      )
    })
  })

  describe('Filter Functionality', () => {
    it('renders filter dropdown with default value', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })

      // Filter dropdown shows "All Companies" by default
      expect(screen.getByText('All Companies')).toBeInTheDocument()
    })

    // Note: Testing Radix UI Select interactions is complex in jsdom due to portal rendering
    // The filter functionality is verified through integration tests instead
  })

  describe('Delete Functionality', () => {
    it('shows confirmation dialog when delete button clicked', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)
      vi.mocked(global.confirm).mockReturnValue(false)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })

      const user = userEvent.setup()
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      expect(global.confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this company? This will unlink all associated declarations.'
      )
    })

    it('deletes company when confirmed', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)
      vi.mocked(api.deleteCompany).mockResolvedValue(undefined)
      vi.mocked(global.confirm).mockReturnValue(true)

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      })

      render(
        <QueryClientProvider client={queryClient}>
          <CompaniesPage />
        </QueryClientProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })

      const user = userEvent.setup()
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      await waitFor(() => {
        expect(api.deleteCompany).toHaveBeenCalledWith(
          'importer-1',
          'importers'
        )
      })
    })

    it('does not delete company when cancelled', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)
      vi.mocked(global.confirm).mockReturnValue(false)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })

      const user = userEvent.setup()
      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      expect(api.deleteCompany).not.toHaveBeenCalled()
    })
  })

  describe('Navigation', () => {
    it('navigates to add company page when clicking "Add Company" button', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      const user = userEvent.setup()
      const addButton = screen.getByRole('button', { name: /add company/i })
      await user.click(addButton)

      expect(mockPush).toHaveBeenCalledWith('/companies/new')
    })

    it('navigates to company details when clicking "View Details" button', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })

      const user = userEvent.setup()
      const viewButtons = screen.getAllByRole('button', {
        name: /view details/i,
      })
      await user.click(viewButtons[0])

      expect(mockPush).toHaveBeenCalledWith(
        '/companies/importer-1?type=importers'
      )
    })
  })

  describe('Pagination', () => {
    it('renders pagination controls when total_pages > 1', async () => {
      const multiPageResponse: CompanyListResponse = {
        items: mockImporters,
        total: 50,
        page: 1,
        limit: 20,
        total_pages: 3,
      }

      vi.mocked(api.getCompanies).mockResolvedValue(multiPageResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(
          screen.getByText('Page 1 of 3 (50 companies)')
        ).toBeInTheDocument()
      })

      expect(
        screen.getByRole('button', { name: /previous/i })
      ).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
    })

    it('disables Previous button on first page', async () => {
      const multiPageResponse: CompanyListResponse = {
        items: mockImporters,
        total: 50,
        page: 1,
        limit: 20,
        total_pages: 3,
      }

      vi.mocked(api.getCompanies).mockResolvedValue(multiPageResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        const prevButton = screen.getByRole('button', { name: /previous/i })
        expect(prevButton).toBeDisabled()
      })
    })

    it('does not render pagination when total_pages <= 1', async () => {
      vi.mocked(api.getCompanies).mockResolvedValue(mockImportersResponse)

      renderWithQueryClient(<CompaniesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Importer A')).toBeInTheDocument()
      })

      expect(
        screen.queryByRole('button', { name: /previous/i })
      ).not.toBeInTheDocument()
      expect(
        screen.queryByRole('button', { name: /next/i })
      ).not.toBeInTheDocument()
    })
  })
})
