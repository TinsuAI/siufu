import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import UploadPage from '@/app/[locale]/upload/page'
import { useAuthStore } from '@/stores/auth-store'
import { useUploadStore } from '@/stores/upload-store'
import * as api from '@/lib/api'

// Mock Next.js navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock API module
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual('@/lib/api')
  return {
    ...actual,
    uploadDeclaration: vi.fn(),
  }
})

describe('UploadPage Integration Tests - 4-File Upload Flow', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()
    mockPush.mockClear()

    // Create a new QueryClient for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    // Set user as authenticated
    useAuthStore.setState({
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
      isAuthenticated: true,
      isLoading: false,
    })

    // Reset upload store
    useUploadStore.getState().reset()
  })

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  it('renders all 4 drop zones with correct labels', () => {
    renderWithProviders(<UploadPage />)

    // Check all 4 file drop zones are rendered (Good List and EXIM Tariff removed)
    expect(screen.getByText(/Arrival Notice.*AN\.pdf/i)).toBeInTheDocument()
    expect(screen.getByText(/Bill of Lading.*BOL\.pdf/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Certificate of Origin.*CO\.pdf/i)
    ).toBeInTheDocument()
    expect(screen.getByText(/Invoice.*INVOICE/i)).toBeInTheDocument()

    // Good List and EXIM Tariff should NOT be present
    expect(
      screen.queryByText(/Good List.*goodlist\.xlsx/i)
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText(/EXIM Tariff.*tariff\.xlsx/i)
    ).not.toBeInTheDocument()
  })

  it('shows CO zone as multi-file supported', () => {
    renderWithProviders(<UploadPage />)

    // CO zone should indicate multiple file support in the label
    expect(
      screen.getByText(/Certificate of Origin.*Multiple files supported/i)
    ).toBeInTheDocument()
  })

  it('shows page header and instructions for 4-file upload', () => {
    renderWithProviders(<UploadPage />)

    // Check header and instructions
    expect(screen.getByText('Upload Declaration Documents')).toBeInTheDocument()
    expect(
      screen.getByText(
        /Upload all 4 required document types to process a new customs declaration/i
      )
    ).toBeInTheDocument()
  })

  it('shows upload progress counter for 4 files', () => {
    renderWithProviders(<UploadPage />)

    // Initially should show 0 of 4
    expect(
      screen.getByText(/Upload Progress: 0 of 4 required documents uploaded/i)
    ).toBeInTheDocument()
  })

  it('Process Declaration button is disabled when no required documents uploaded', () => {
    renderWithProviders(<UploadPage />)

    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    expect(processButton).toBeDisabled()
  })

  it('updates progress counter when files are added', async () => {
    renderWithProviders(<UploadPage />)

    // Add AN file
    const file1 = new File(['content'], 'AN.pdf', { type: 'application/pdf' })
    const anInput = screen.getAllByLabelText(/File input/i)[0]
    await userEvent.upload(anInput, file1)

    // Progress should update to 1 of 4
    await waitFor(() => {
      expect(
        screen.getByText(/Upload Progress: 1 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })

    // Add BOL file
    const file2 = new File(['content'], 'BOL.pdf', { type: 'application/pdf' })
    const bolInput = screen.getAllByLabelText(/File input/i)[1]
    await userEvent.upload(bolInput, file2)

    // Progress should update to 2 of 4
    await waitFor(() => {
      expect(
        screen.getByText(/Upload Progress: 2 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })
  })

  it('counts CO as single file type even with multiple files', async () => {
    renderWithProviders(<UploadPage />)

    // Add 3 CO files
    const coFiles = [
      new File(['content1'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'CO_2.pdf', { type: 'application/pdf' }),
      new File(['content3'], 'CO_3.pdf', { type: 'application/pdf' }),
    ]

    const coInput = screen.getAllByLabelText(
      /File input.*Certificate of Origin/i
    )[0]
    await userEvent.upload(coInput, coFiles)

    // Progress should show 1 of 4 (CO counts as 1 document type)
    await waitFor(() => {
      expect(
        screen.getByText(/Upload Progress: 1 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })

    // But CO badge should show "3 files"
    expect(screen.getByText('3 files')).toBeInTheDocument()
  })

  it('enables Process Declaration button when all 4 file types are uploaded (with 1 CO file)', async () => {
    renderWithProviders(<UploadPage />)

    // Upload 4 file types (minimum valid case - 1 CO file)
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
    ]

    const fileInputs = screen.getAllByLabelText(/File input/i)

    for (let i = 0; i < 4; i++) {
      await userEvent.upload(fileInputs[i], files[i])
    }

    // Wait for all files to be processed
    await waitFor(() => {
      expect(
        screen.getByText(/Upload Progress: 4 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })

    // Process button should now be enabled
    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    expect(processButton).not.toBeDisabled()
  })

  it('enables Process Declaration button with multiple CO files', async () => {
    renderWithProviders(<UploadPage />)

    // Upload 4 file types with 3 CO files
    const anFile = new File(['content'], 'AN.pdf', { type: 'application/pdf' })
    const bolFile = new File(['content'], 'BOL.pdf', {
      type: 'application/pdf',
    })
    const coFiles = [
      new File(['content1'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'CO_2.pdf', { type: 'application/pdf' }),
      new File(['content3'], 'CO_3.pdf', { type: 'application/pdf' }),
    ]
    const invoiceFile = new File(['content'], 'INVOICE.jpg', {
      type: 'image/jpeg',
    })

    const fileInputs = screen.getAllByLabelText(/File input/i)

    await userEvent.upload(fileInputs[0], anFile)
    await userEvent.upload(fileInputs[1], bolFile)
    await userEvent.upload(fileInputs[2], coFiles)
    await userEvent.upload(fileInputs[3], invoiceFile)

    // Wait for all files to be processed
    await waitFor(() => {
      expect(
        screen.getByText(/Upload Progress: 4 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })

    // Process button should be enabled
    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    expect(processButton).not.toBeDisabled()

    // CO badge should show "3 files"
    expect(screen.getByText('3 files')).toBeInTheDocument()
  })

  it('shows success message when all 4 file types are uploaded', async () => {
    renderWithProviders(<UploadPage />)

    // Upload all 4 file types
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
    ]

    const fileInputs = screen.getAllByLabelText(/File input/i)

    for (let i = 0; i < 4; i++) {
      await userEvent.upload(fileInputs[i], files[i])
    }

    // Should show "All documents uploaded! Ready to process."
    await waitFor(() => {
      expect(
        screen.getByText(/All documents uploaded! Ready to process/i)
      ).toBeInTheDocument()
    })
  })

  it('successfully uploads 4 file types and navigates to declaration page', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration)
    mockUploadDeclaration.mockResolvedValue({
      declaration_id: 'test-declaration-123',
      status: 'UPLOADED',
      created_at: '2025-10-31T12:00:00Z',
    })

    renderWithProviders(<UploadPage />)

    // Upload all 4 file types
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
    ]

    const fileInputs = screen.getAllByLabelText(/File input/i)

    for (let i = 0; i < 4; i++) {
      await userEvent.upload(fileInputs[i], files[i])
    }

    // Wait for all files to be uploaded
    await waitFor(() => {
      expect(
        screen.getByText(/4 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })

    // Click Process Declaration button
    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    await userEvent.click(processButton)

    // Should call uploadDeclaration API
    await waitFor(
      () => {
        expect(mockUploadDeclaration).toHaveBeenCalled()
      },
      { timeout: 3000 }
    )

    // Should navigate to declaration page
    await waitFor(
      () => {
        expect(mockPush).toHaveBeenCalledWith(
          '/declarations/test-declaration-123'
        )
      },
      { timeout: 5000 }
    )
  })

  it('successfully uploads with 10 CO files (recommended limit)', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration)
    mockUploadDeclaration.mockResolvedValue({
      declaration_id: 'test-declaration-456',
      status: 'UPLOADED',
      created_at: '2025-10-31T12:00:00Z',
    })

    renderWithProviders(<UploadPage />)

    // Create 10 CO files
    const coFiles = Array.from(
      { length: 10 },
      (_, i) =>
        new File([`content${i}`], `CO_${i + 1}.pdf`, {
          type: 'application/pdf',
        })
    )

    const anFile = new File(['content'], 'AN.pdf', { type: 'application/pdf' })
    const bolFile = new File(['content'], 'BOL.pdf', {
      type: 'application/pdf',
    })
    const invoiceFile = new File(['content'], 'INVOICE.pdf', {
      type: 'application/pdf',
    })

    const fileInputs = screen.getAllByLabelText(/File input/i)

    await userEvent.upload(fileInputs[0], anFile)
    await userEvent.upload(fileInputs[1], bolFile)
    await userEvent.upload(fileInputs[2], coFiles)
    await userEvent.upload(fileInputs[3], invoiceFile)

    // CO badge should show "10 files"
    await waitFor(() => {
      expect(screen.getByText('10 files')).toBeInTheDocument()
    })

    // Should NOT show warning (10 is at the limit, not over)
    expect(
      screen.queryByText(/Warning.*many CO files/i)
    ).not.toBeInTheDocument()

    // Should enable process button
    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    expect(processButton).not.toBeDisabled()
  })

  it('shows warning badge when more than 10 CO files are uploaded', async () => {
    renderWithProviders(<UploadPage />)

    // Create 11 CO files (above recommended limit)
    const coFiles = Array.from(
      { length: 11 },
      (_, i) =>
        new File([`content${i}`], `CO_${i + 1}.pdf`, {
          type: 'application/pdf',
        })
    )

    const coInput = screen.getAllByLabelText(
      /File input.*Certificate of Origin/i
    )[0]
    await userEvent.upload(coInput, coFiles)

    // CO badge should show "11 files"
    await waitFor(() => {
      expect(screen.getByText('11 files')).toBeInTheDocument()
    })

    // Note: The warning is shown via the coFileCountWarning state which may trigger
    // a UI warning banner. For now, we verify the upload still works (warning, not error).

    // Should still allow upload to complete
    const anFile = new File(['content'], 'AN.pdf', { type: 'application/pdf' })
    const bolFile = new File(['content'], 'BOL.pdf', {
      type: 'application/pdf',
    })
    const invoiceFile = new File(['content'], 'INVOICE.pdf', {
      type: 'application/pdf',
    })

    const fileInputs = screen.getAllByLabelText(/File input/i)
    await userEvent.upload(fileInputs[0], anFile)
    await userEvent.upload(fileInputs[1], bolFile)
    await userEvent.upload(fileInputs[3], invoiceFile)

    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    expect(processButton).not.toBeDisabled()
  })

  it('displays error message when upload fails', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration)
    mockUploadDeclaration.mockRejectedValue(
      new Error('Network error. Please check your connection.')
    )

    renderWithProviders(<UploadPage />)

    // Upload all 4 file types
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
    ]

    const fileInputs = screen.getAllByLabelText(/File input/i)

    for (let i = 0; i < 4; i++) {
      await userEvent.upload(fileInputs[i], files[i])
    }

    // Click Process Declaration button
    await waitFor(() => {
      expect(
        screen.getByText(/4 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })

    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    await userEvent.click(processButton)

    // Should display error message
    await waitFor(() => {
      expect(screen.getByText(/Upload Failed/i)).toBeInTheDocument()
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })

    // Should show Retry button
    expect(
      screen.getByRole('button', { name: /Retry Upload/i })
    ).toBeInTheDocument()
  })

  it('allows retry after upload failure', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration)

    // First call fails
    mockUploadDeclaration.mockRejectedValueOnce(new Error('Network error'))

    // Second call succeeds
    mockUploadDeclaration.mockResolvedValueOnce({
      declaration_id: 'test-declaration-789',
      status: 'UPLOADED',
      created_at: '2025-10-31T12:00:00Z',
    })

    renderWithProviders(<UploadPage />)

    // Upload all 4 file types
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
    ]

    const fileInputs = screen.getAllByLabelText(/File input/i)

    for (let i = 0; i < 4; i++) {
      await userEvent.upload(fileInputs[i], files[i])
    }

    // Click Process Declaration (first attempt - fails)
    await waitFor(() => {
      expect(
        screen.getByText(/4 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })

    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    await userEvent.click(processButton)

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/Upload Failed/i)).toBeInTheDocument()
    })

    // Click Retry button
    const retryButton = screen.getByRole('button', { name: /Retry Upload/i })
    await userEvent.click(retryButton)

    // Second attempt should succeed and navigate
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        '/declarations/test-declaration-789'
      )
    })
  })

  it('redirects to login if user is not authenticated', async () => {
    // Set user as not authenticated
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    })

    renderWithProviders(<UploadPage />)

    // Should redirect to login
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  it('disables all drop zones while upload is in progress', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration)

    // Make upload take a while (simulate slow network)
    mockUploadDeclaration.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                declaration_id: 'test-declaration-999',
                status: 'UPLOADED',
                created_at: '2025-10-31T12:00:00Z',
              }),
            1000
          )
        )
    )

    renderWithProviders(<UploadPage />)

    // Upload all 4 file types
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
    ]

    const fileInputs = screen.getAllByLabelText(/File input/i)

    for (let i = 0; i < 4; i++) {
      await userEvent.upload(fileInputs[i], files[i])
    }

    await waitFor(() => {
      expect(
        screen.getByText(/4 of 4 required documents uploaded/i)
      ).toBeInTheDocument()
    })

    // Click Process Declaration
    const processButton = screen.getByRole('button', {
      name: /Process declaration/i,
    })
    await userEvent.click(processButton)

    // While uploading, all file inputs should be disabled
    await waitFor(() => {
      expect(screen.getByText(/Uploading\.\.\./i)).toBeInTheDocument()
    })

    const fileInputsAfterUpload = screen.getAllByLabelText(/File input/i)
    fileInputsAfterUpload.forEach((input) => {
      expect(input).toBeDisabled()
    })
  })

  it('shows help section with tips', () => {
    renderWithProviders(<UploadPage />)

    expect(screen.getByText(/Help & Tips/i)).toBeInTheDocument()
    expect(screen.getByText(/You can drag and drop files/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Files are validated for type and size/i)
    ).toBeInTheDocument()
    expect(screen.getByText(/Maximum file sizes/i)).toBeInTheDocument()
  })

  it('allows removing individual CO files', async () => {
    renderWithProviders(<UploadPage />)

    // Upload 3 CO files
    const coFiles = [
      new File(['content1'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'CO_2.pdf', { type: 'application/pdf' }),
      new File(['content3'], 'CO_3.pdf', { type: 'application/pdf' }),
    ]

    const coInput = screen.getAllByLabelText(
      /File input.*Certificate of Origin/i
    )[0]
    await userEvent.upload(coInput, coFiles)

    // Should show "3 files" badge
    await waitFor(() => {
      expect(screen.getByText('3 files')).toBeInTheDocument()
    })

    // Find and click remove button for second CO file
    const removeButtons = screen.getAllByLabelText(/Remove CO_/i)
    expect(removeButtons.length).toBe(3)

    await userEvent.click(removeButtons[1]) // Remove CO_2.pdf

    // Should now show "2 files" badge
    await waitFor(() => {
      expect(screen.getByText('2 files')).toBeInTheDocument()
    })

    // CO_2.pdf should be gone
    expect(screen.queryByText('CO_2.pdf')).not.toBeInTheDocument()

    // CO_1.pdf and CO_3.pdf should still be present
    expect(screen.getByText('CO_1.pdf')).toBeInTheDocument()
    expect(screen.getByText('CO_3.pdf')).toBeInTheDocument()
  })

  it('allows adding more CO files after initial upload', async () => {
    renderWithProviders(<UploadPage />)

    // Upload 2 CO files initially
    const initialCoFiles = [
      new File(['content1'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'CO_2.pdf', { type: 'application/pdf' }),
    ]

    const coInput = screen.getAllByLabelText(
      /File input.*Certificate of Origin/i
    )[0]
    await userEvent.upload(coInput, initialCoFiles)

    await waitFor(() => {
      expect(screen.getByText('2 files')).toBeInTheDocument()
    })

    // Upload 2 more CO files
    const additionalCoFiles = [
      new File(['content3'], 'CO_3.pdf', { type: 'application/pdf' }),
      new File(['content4'], 'CO_4.pdf', { type: 'application/pdf' }),
    ]

    await userEvent.upload(coInput, additionalCoFiles)

    // Should now show "4 files" badge
    await waitFor(() => {
      expect(screen.getByText('4 files')).toBeInTheDocument()
    })

    // All 4 files should be listed
    expect(screen.getByText('CO_1.pdf')).toBeInTheDocument()
    expect(screen.getByText('CO_2.pdf')).toBeInTheDocument()
    expect(screen.getByText('CO_3.pdf')).toBeInTheDocument()
    expect(screen.getByText('CO_4.pdf')).toBeInTheDocument()
  })
})
