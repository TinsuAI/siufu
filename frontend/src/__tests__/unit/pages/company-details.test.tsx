/**
 * Unit tests for Company Details/Edit Page
 * Tests viewing, editing, and deleting company details
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CompanyDetailsPage from '@/app/[locale]/companies/[id]/page'
import * as hooks from '@/hooks/use-companies'
import type { ImporterDetail, ExporterDetail } from '@/types/company'

// Mock Next.js navigation
const mockPush = vi.fn()
const mockSearchParams = new URLSearchParams()
vi.mock('@/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))
vi.mock('next/navigation', () => ({
  useSearchParams: () => mockSearchParams,
}))

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// Mock hooks
vi.mock('@/hooks/use-companies', () => ({
  useCompany: vi.fn(),
  useUpdateCompany: vi.fn(),
  useDeleteCompany: vi.fn(),
}))

afterEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
  mockSearchParams.delete('type')
})

// Test data
const mockImporter: ImporterDetail = {
  id: 'importer-1',
  tax_code: '1234567890',
  name: 'Test Importer Company',
  postal_code: '700000',
  address: '123 Test Street, District 1',
  phone: '+84 28 1234 5678',
  name_normalized: 'test importer company',
  organization_id: 'org-1',
  first_seen_declaration_id: 'decl-1',
  last_seen_declaration_id: 'decl-10',
  declaration_count: 10,
  is_verified: true,
  confidence_score: 0.95,
  last_reviewed_by_user_id: 'user-1',
  last_reviewed_at: '2025-01-10T10:00:00Z',
  created_at: '2025-01-01T10:00:00Z',
  updated_at: '2025-01-15T10:00:00Z',
  deleted_at: null,
}

const mockExporter: ExporterDetail = {
  id: 'exporter-1',
  name: 'Test Exporter Company',
  name_normalized: 'test exporter company',
  country_code: 'CN',
  address_line1: '456 Export Road',
  address_line2: 'Shanghai',
  address_line3: 'China',
  organization_id: 'org-1',
  first_seen_declaration_id: 'decl-1',
  last_seen_declaration_id: 'decl-20',
  declaration_count: 20,
  is_verified: false,
  confidence_score: 0.85,
  last_reviewed_by_user_id: 'user-1',
  last_reviewed_at: '2025-01-10T10:00:00Z',
  created_at: '2025-01-01T10:00:00Z',
  updated_at: '2025-01-15T10:00:00Z',
  deleted_at: null,
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

type UseCompanyResult = ReturnType<typeof hooks.useCompany>
type UseUpdateCompanyResult = ReturnType<typeof hooks.useUpdateCompany>
type UseDeleteCompanyResult = ReturnType<typeof hooks.useDeleteCompany>

const mockUseCompanyReturn = (overrides: Partial<UseCompanyResult>) =>
  ({
    data: undefined,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    isError: false,
    isSuccess: false,
    ...overrides,
  }) as unknown as UseCompanyResult

const mockUseUpdateCompanyReturn = (
  overrides?: Partial<UseUpdateCompanyResult>
) =>
  ({
    mutateAsync: vi.fn(),
    isPending: false,
    ...overrides,
  }) as unknown as UseUpdateCompanyResult

const mockUseDeleteCompanyReturn = (
  overrides?: Partial<UseDeleteCompanyResult>
) =>
  ({
    mutateAsync: vi.fn(),
    isPending: false,
    ...overrides,
  }) as unknown as UseDeleteCompanyResult

const mockRouteParams = (id: string) => {
  vi.spyOn(React, 'use').mockReturnValue({ id })
}

describe('CompanyDetailsPage', () => {
  describe('Loading State', () => {
    it('displays loading message while fetching company', () => {
      mockSearchParams.set('type', 'importers')

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ isLoading: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      // Mock params
      const params = Promise.resolve({ id: 'importer-1' })
      mockRouteParams('importer-1')

      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(screen.getByText('Loading company details...')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('displays error message when company not found', () => {
      mockSearchParams.set('type', 'importers')

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({
          error: new Error('Company not found'),
          isError: true,
        })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      const params = Promise.resolve({ id: 'invalid-id' })
      mockRouteParams('invalid-id')

      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(
        screen.getByText(/error loading company: company not found/i)
      ).toBeInTheDocument()
    })
  })

  describe('Importer Details Display', () => {
    beforeEach(() => {
      mockSearchParams.set('type', 'importers')

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      mockRouteParams('importer-1')
    })

    it('renders company name in header', () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(screen.getByText('Test Importer Company')).toBeInTheDocument()
    })

    it('displays tax code in subtitle for importers', () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(screen.getByText('Tax Code: 1234567890')).toBeInTheDocument()
    })

    it('displays verified badge for verified companies', () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(screen.getByText('Verified')).toBeInTheDocument()
    })

    it('renders all importer form fields in read-only mode', () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const taxCodeInput = screen.getByLabelText(
        /tax code/i
      ) as HTMLInputElement
      const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement
      const postalCodeInput = screen.getByLabelText(
        /postal code/i
      ) as HTMLInputElement
      const phoneInput = screen.getByLabelText(/phone/i) as HTMLInputElement
      const addressInput = screen.getByLabelText(/address/i) as HTMLInputElement

      expect(taxCodeInput).toBeDisabled()
      expect(nameInput).toBeDisabled()
      expect(postalCodeInput).toBeDisabled()
      expect(phoneInput).toBeDisabled()
      expect(addressInput).toBeDisabled()

      expect(taxCodeInput.value).toBe('1234567890')
      expect(nameInput.value).toBe('Test Importer Company')
      expect(postalCodeInput.value).toBe('700000')
      expect(phoneInput.value).toBe('+84 28 1234 5678')
      expect(addressInput.value).toBe('123 Test Street, District 1')
    })

    it('displays statistics section with correct values', () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(screen.getByText('Statistics')).toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument() // declaration count
      expect(screen.getByText('95%')).toBeInTheDocument() // confidence score
    })

    it('renders Edit and Delete buttons in view mode', () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /delete/i })
      ).toBeInTheDocument()
    })

    it('renders Back to Companies button', () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(
        screen.getByRole('button', { name: /back to companies/i })
      ).toBeInTheDocument()
    })
  })

  describe('Exporter Details Display', () => {
    beforeEach(() => {
      mockSearchParams.set('type', 'exporters')

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockExporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      mockRouteParams('exporter-1')
    })

    it('displays country code in subtitle for exporters', () => {
      const params = Promise.resolve({ id: 'exporter-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(screen.getByText('Country: CN')).toBeInTheDocument()
    })

    it('displays unverified badge for unverified companies', () => {
      const params = Promise.resolve({ id: 'exporter-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      expect(screen.getByText('Unverified')).toBeInTheDocument()
    })

    it('renders all exporter form fields in read-only mode', () => {
      const params = Promise.resolve({ id: 'exporter-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const nameInput = screen.getByLabelText(/^name/i) as HTMLInputElement
      const countryCodeInput = screen.getByLabelText(
        /country code/i
      ) as HTMLInputElement
      const addressLine1Input = screen.getByLabelText(
        /address line 1/i
      ) as HTMLInputElement
      const addressLine2Input = screen.getByLabelText(
        /address line 2/i
      ) as HTMLInputElement
      const addressLine3Input = screen.getByLabelText(
        /address line 3/i
      ) as HTMLInputElement

      expect(nameInput).toBeDisabled()
      expect(countryCodeInput).toBeDisabled()
      expect(addressLine1Input).toBeDisabled()
      expect(addressLine2Input).toBeDisabled()
      expect(addressLine3Input).toBeDisabled()

      expect(nameInput.value).toBe('Test Exporter Company')
      expect(countryCodeInput.value).toBe('CN')
      expect(addressLine1Input.value).toBe('456 Export Road')
      expect(addressLine2Input.value).toBe('Shanghai')
      expect(addressLine3Input.value).toBe('China')
    })
  })

  describe('Edit Mode', () => {
    beforeEach(() => {
      mockSearchParams.set('type', 'importers')

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      mockRouteParams('importer-1')
    })

    it('enables form inputs when Edit button clicked', async () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const editButton = screen.getByRole('button', { name: /^edit$/i })
      await user.click(editButton)

      const nameInput = screen.getByLabelText(/^name/i) as HTMLInputElement
      expect(nameInput).not.toBeDisabled()
    })

    it('shows Save and Cancel buttons in edit mode', async () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const editButton = screen.getByRole('button', { name: /^edit$/i })
      await user.click(editButton)

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /cancel/i })
      ).toBeInTheDocument()
      expect(
        screen.queryByRole('button', { name: /^edit$/i })
      ).not.toBeInTheDocument()
    })

    it('hides Edit and Delete buttons in edit mode', async () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const editButton = screen.getByRole('button', { name: /^edit$/i })
      await user.click(editButton)

      expect(
        screen.queryByRole('button', { name: /^edit$/i })
      ).not.toBeInTheDocument()
      expect(
        screen.queryByRole('button', { name: /^delete$/i })
      ).not.toBeInTheDocument()
    })

    it('allows editing form fields', async () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const editButton = screen.getByRole('button', { name: /^edit$/i })
      await user.click(editButton)

      const nameInput = screen.getByLabelText(/^name/i) as HTMLInputElement
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Company Name')

      expect(nameInput.value).toBe('Updated Company Name')
    })

    it('cancels editing and resets form when Cancel clicked', async () => {
      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const editButton = screen.getByRole('button', { name: /^edit$/i })
      await user.click(editButton)

      const nameInput = screen.getByLabelText(/^name/i) as HTMLInputElement
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Name')

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /^edit$/i })
        ).toBeInTheDocument()
      })

      // Form should be reset to original value
      const nameInputAfterCancel = screen.getByLabelText(
        /^name/i
      ) as HTMLInputElement
      expect(nameInputAfterCancel.value).toBe('Test Importer Company')
      expect(nameInputAfterCancel).toBeDisabled()
    })
  })

  describe('Save Functionality', () => {
    it('calls update mutation when Save clicked', async () => {
      mockSearchParams.set('type', 'importers')

      const mockMutateAsync = vi.fn().mockResolvedValue(mockImporter)

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn({ mutateAsync: mockMutateAsync })
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      mockRouteParams('importer-1')

      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const editButton = screen.getByRole('button', { name: /^edit$/i })
      await user.click(editButton)

      const nameInput = screen.getByLabelText(/^name/i) as HTMLInputElement
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Company')

      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          id: 'importer-1',
          type: 'importers',
          data: expect.objectContaining({
            name: 'Updated Company',
          }),
        })
      })
    })

    it('exits edit mode after successful save', async () => {
      mockSearchParams.set('type', 'importers')

      const mockMutateAsync = vi.fn().mockResolvedValue(mockImporter)

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn({ mutateAsync: mockMutateAsync })
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      mockRouteParams('importer-1')

      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const editButton = screen.getByRole('button', { name: /^edit$/i })
      await user.click(editButton)

      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /^edit$/i })
        ).toBeInTheDocument()
      })
    })
  })

  describe('Delete Functionality', () => {
    const originalConfirm = global.confirm

    afterEach(() => {
      global.confirm = originalConfirm
    })

    it('shows confirmation dialog when Delete clicked', async () => {
      mockSearchParams.set('type', 'importers')
      global.confirm = vi.fn().mockReturnValue(false)

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      mockRouteParams('importer-1')

      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const deleteButton = screen.getByRole('button', { name: /^delete$/i })
      await user.click(deleteButton)

      expect(global.confirm).toHaveBeenCalledWith(
        expect.stringContaining(
          'Are you sure you want to delete Test Importer Company?'
        )
      )
    })

    it('calls delete mutation when confirmed', async () => {
      mockSearchParams.set('type', 'importers')
      global.confirm = vi.fn().mockReturnValue(true)

      const mockDeleteAsync = vi.fn().mockResolvedValue(undefined)

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn({ mutateAsync: mockDeleteAsync })
      )

      mockRouteParams('importer-1')

      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const deleteButton = screen.getByRole('button', { name: /^delete$/i })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(mockDeleteAsync).toHaveBeenCalledWith({
          id: 'importer-1',
          type: 'importers',
        })
      })
    })

    it('navigates to companies list after successful deletion', async () => {
      mockSearchParams.set('type', 'importers')
      global.confirm = vi.fn().mockReturnValue(true)

      const mockDeleteAsync = vi.fn().mockResolvedValue(undefined)

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn({ mutateAsync: mockDeleteAsync })
      )

      mockRouteParams('importer-1')

      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const deleteButton = screen.getByRole('button', { name: /^delete$/i })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/companies')
      })
    })

    it('does not delete when cancelled', async () => {
      mockSearchParams.set('type', 'importers')
      global.confirm = vi.fn().mockReturnValue(false)

      const mockDeleteAsync = vi.fn()

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn({ mutateAsync: mockDeleteAsync })
      )

      mockRouteParams('importer-1')

      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const deleteButton = screen.getByRole('button', { name: /^delete$/i })
      await user.click(deleteButton)

      expect(mockDeleteAsync).not.toHaveBeenCalled()
    })
  })

  describe('Navigation', () => {
    it('navigates to companies list when Back button clicked', async () => {
      mockSearchParams.set('type', 'importers')

      vi.mocked(hooks.useCompany).mockReturnValue(
        mockUseCompanyReturn({ data: mockImporter, isSuccess: true })
      )

      vi.mocked(hooks.useUpdateCompany).mockReturnValue(
        mockUseUpdateCompanyReturn()
      )

      vi.mocked(hooks.useDeleteCompany).mockReturnValue(
        mockUseDeleteCompanyReturn()
      )

      mockRouteParams('importer-1')

      const params = Promise.resolve({ id: 'importer-1' })
      renderWithQueryClient(<CompanyDetailsPage params={params} />)

      const user = userEvent.setup()
      const backButton = screen.getByRole('button', {
        name: /back to companies/i,
      })
      await user.click(backButton)

      expect(mockPush).toHaveBeenCalledWith('/companies')
    })
  })
})
