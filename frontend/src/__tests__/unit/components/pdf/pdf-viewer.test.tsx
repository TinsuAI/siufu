import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PDFViewer } from '@/components/pdf/pdf-viewer'
import * as api from '@/lib/api'
import { useUIStore } from '@/stores/ui-store'

// Mock the API module
vi.mock('@/lib/api', () => ({
  getPDFFile: vi.fn(),
  getDeclarationMetadata: vi.fn(),
}))

// Mock react-pdf to avoid PDF.js worker issues in tests
vi.mock('react-pdf', () => ({
  /* eslint-disable @typescript-eslint/no-explicit-any */
  Document: (() => {
    let lastFile: any = null
    const MockDocument = ({ children, file, onLoadSuccess }: any) => {
      // Only call onLoadSuccess when file changes (mimics real react-pdf behavior)
      if (file && file !== lastFile && onLoadSuccess) {
        lastFile = file
        setTimeout(() => {
          onLoadSuccess({ numPages: 5 })
        }, 0)
      }
      return <div data-testid="pdf-document">{children}</div>
    }
    MockDocument.displayName = 'MockDocument'
    return MockDocument
  })(),
  Page: ({ pageNumber, width, onLoadSuccess }: any) => {
    // Simulate page load success with text extraction
    setTimeout(() => {
      onLoadSuccess?.({
        pageNumber,
        getTextContent: async () => ({
          items: [{ str: `Sample text on page ${pageNumber}` }],
        }),
      })
    }, 0)
    // Differentiate between thumbnail (width=160) and main viewer
    const isThumbnail = width === 160
    const testId = isThumbnail
      ? `pdf-thumbnail-${pageNumber}`
      : `pdf-page-${pageNumber}`
    return <div data-testid={testId}>Page {pageNumber}</div>
  },
  pdfjs: {
    version: '3.11.0',
    GlobalWorkerOptions: { workerSrc: '' },
  },
  /* eslint-enable @typescript-eslint/no-explicit-any */
}))

describe('PDFViewer', () => {
  let queryClient: QueryClient
  const user = userEvent.setup()

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
    vi.clearAllMocks()

    // Reset Zustand UI store to default state
    useUIStore.getState().resetPdfState()

    // Generate unique blob URL for each test to avoid mock caching
    const uniqueId = `${Date.now()}-${Math.random()}`
    global.URL.createObjectURL = () => `blob:mock-url-${uniqueId}`

    // Mock PDF file response
    const mockPdfBlob = new Blob(['PDF content'], { type: 'application/pdf' })
    vi.mocked(api.getPDFFile).mockResolvedValue(mockPdfBlob)

    // Mock declaration metadata
    vi.mocked(api.getDeclarationMetadata).mockResolvedValue({
      id: 'decl-123',
      uploaded_files: {
        arrival_notice: 'AN.pdf',
        bill_of_lading: 'BOL.pdf',
        certificate_of_origin: ['CO_1.pdf', 'CO_2.pdf'],
        invoice: 'INVOICE.pdf',
      },
    })
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('should render PDF document successfully', async () => {
    // Act
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    // Assert - Loading state
    expect(screen.getByText('Loading PDF...')).toBeInTheDocument()

    // Wait for PDF to load
    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Assert - PDF loaded
    expect(screen.getByTestId('pdf-page-1')).toBeInTheDocument()
  })

  it('should navigate to next and previous pages', async () => {
    // Arrange
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Assert - Initially on page 1
    expect(screen.getByDisplayValue('1')).toBeInTheDocument()
    expect(screen.getByText('/ 5')).toBeInTheDocument()

    // Act - Click next page
    const nextButton = screen.getByTitle('Next Page')
    await user.click(nextButton)

    // Assert - Page 2
    await waitFor(() => {
      expect(screen.getByDisplayValue('2')).toBeInTheDocument()
    })

    // Act - Click previous page
    const prevButton = screen.getByTitle('Previous Page')
    await user.click(prevButton)

    // Assert - Back to page 1
    await waitFor(() => {
      expect(screen.getByDisplayValue('1')).toBeInTheDocument()
    })
  })

  it('should update zoom level with zoom controls', async () => {
    // Arrange
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Assert - Initial zoom is 100%
    expect(screen.getByText('100%')).toBeInTheDocument()

    // Act - Zoom in
    const zoomInButton = screen.getByTitle('Zoom In')
    await user.click(zoomInButton)

    // Assert - Zoom increased to 125%
    await waitFor(() => {
      expect(screen.getByText('125%')).toBeInTheDocument()
    })

    // Act - Zoom out
    const zoomOutButton = screen.getByTitle('Zoom Out')
    await user.click(zoomOutButton)

    // Assert - Back to 100%
    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument()
    })
  })

  it('should toggle thumbnail sidebar visibility', async () => {
    // Arrange
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Assert - Sidebar thumbnails visible by default
    expect(screen.getByTestId('pdf-thumbnail-1')).toBeInTheDocument()
    expect(screen.getByTestId('pdf-thumbnail-2')).toBeInTheDocument()

    // Act - Toggle sidebar off
    const toggleButton = screen.getByTitle('Toggle Sidebar')
    await user.click(toggleButton)

    // Assert - Sidebar thumbnails hidden
    await waitFor(() => {
      expect(screen.queryByTestId('pdf-thumbnail-1')).not.toBeInTheDocument()
      expect(screen.queryByTestId('pdf-thumbnail-2')).not.toBeInTheDocument()
    })

    // Act - Toggle sidebar on
    await user.click(toggleButton)

    // Assert - Sidebar visible again
    await waitFor(() => {
      expect(screen.getByTestId('pdf-thumbnail-1')).toBeInTheDocument()
      expect(screen.getByTestId('pdf-thumbnail-2')).toBeInTheDocument()
    })
  })

  it('should search for text in PDF', async () => {
    // Arrange
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Act - Type search query
    const searchInput = screen.getByPlaceholderText('Search in PDF...')
    await user.type(searchInput, 'sample')

    // Assert - Search results displayed
    await waitFor(
      () => {
        expect(screen.getByText(/1 of/)).toBeInTheDocument()
      },
      { timeout: 5000 }
    )

    // Act - Clear search
    const clearButton = screen.getByTitle('Clear Search')
    await user.click(clearButton)

    // Assert - Search cleared
    await waitFor(() => {
      expect(searchInput).toHaveValue('')
      expect(screen.queryByText(/1 of/)).not.toBeInTheDocument()
    })
  })

  it('should render highlight box when provided', async () => {
    // Arrange
    const highlightBox = {
      page: 1,
      bbox: [100, 100, 200, 50] as [number, number, number, number],
    }

    const { container } = render(
      <PDFViewer
        declarationId="decl-123"
        documentType="INVOICE"
        highlightBox={highlightBox}
      />,
      { wrapper }
    )

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Assert - Highlight box overlay exists
    const highlightOverlay = container.querySelector('.animate-pulse')
    expect(highlightOverlay).toBeInTheDocument()
    expect(highlightOverlay).toHaveClass('border-red-500')
  })

  it('should display error message for missing file (404)', async () => {
    // Arrange - Clear previous mock and setup error response
    vi.mocked(api.getPDFFile).mockClear()
    vi.mocked(api.getPDFFile).mockRejectedValue(
      new Error('File "INVOICE.pdf" not found for this declaration.')
    )

    // Act
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    // Assert - Error displayed
    await waitFor(
      () => {
        expect(screen.getByText('Error loading PDF')).toBeInTheDocument()
      },
      { timeout: 5000 }
    )
    expect(screen.getByText(/File "INVOICE.pdf" not found/)).toBeInTheDocument()
  })

  it('should display loading spinner while PDF loads', () => {
    // Act
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    // Assert - Loading state visible
    expect(screen.getByText('Loading PDF...')).toBeInTheDocument()
  })

  it('should switch between documents using tabs', async () => {
    // Arrange
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Assert - Document tabs are visible
    expect(screen.getByText('Arrival Notice')).toBeInTheDocument()
    expect(screen.getByText('Bill of Lading')).toBeInTheDocument()
    expect(screen.getByText('Invoice')).toBeInTheDocument()

    // Act - Click on Arrival Notice tab
    const anTab = screen.getByText('Arrival Notice')
    await user.click(anTab)

    // Assert - API called with new filename
    await waitFor(() => {
      expect(api.getPDFFile).toHaveBeenCalledWith('decl-123', 'AN.pdf')
    })
  })

  it('should handle page input manually', async () => {
    // Arrange
    render(<PDFViewer declarationId="decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Act - Type page number in input
    const pageInput = screen.getByDisplayValue('1')
    await user.clear(pageInput)
    await user.type(pageInput, '3')
    await user.keyboard('{Enter}')

    // Assert - Page changed to 3
    await waitFor(() => {
      expect(screen.getByTestId('pdf-page-3')).toBeInTheDocument()
    })
  })
})
