import React from 'react'
import {
  describe,
  it,
  expect,
  vi,
  beforeAll,
  afterAll,
  beforeEach,
} from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PDFViewer } from '@/components/pdf/pdf-viewer'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { useUIStore } from '@/stores/ui-store'

// Mock react-pdf
/* eslint-disable @typescript-eslint/no-explicit-any */
vi.mock('react-pdf', () => {
  // Track which callbacks have been called for which files to prevent duplicate calls
  const calledCallbacks = new Map<string, boolean>()

  return {
    Document: ({ children, file, onLoadSuccess }: any) => {
      // Only call onLoadSuccess once per unique callback+file combination
      if (file && onLoadSuccess) {
        const key = file + onLoadSuccess.toString().slice(0, 50)
        if (!calledCallbacks.has(key)) {
          calledCallbacks.set(key, true)
          setTimeout(() => {
            onLoadSuccess({ numPages: 10 })
          }, 0)
        }
      }
      return <div data-testid="pdf-document">{children}</div>
    },
    Page: ({ pageNumber, width, onLoadSuccess }: any) => {
      setTimeout(() => {
        onLoadSuccess?.({
          pageNumber,
          getTextContent: async () => ({
            items: [
              { str: `This is page ${pageNumber} content` },
              { str: 'Sample invoice data' },
            ],
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
  }
})
/* eslint-enable @typescript-eslint/no-explicit-any */

// Setup MSW server for API mocking
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

const server = setupServer(
  // Mock PDF file endpoints
  http.get(`${API_BASE_URL}/declarations/:id/files/:filename`, ({ params }) => {
    const { filename } = params
    const pdfContent = `Mock PDF content for ${filename}`
    return new HttpResponse(pdfContent, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
      },
    })
  }),

  // Mock declaration metadata endpoint
  http.get(`${API_BASE_URL}/declarations/:id`, () => {
    return HttpResponse.json({
      id: 'test-decl-123',
      uploaded_files: {
        arrival_notice: 'AN.pdf',
        bill_of_lading: 'BOL.pdf',
        certificate_of_origin: ['CO_1.pdf', 'CO_2.pdf'],
        invoice: 'INVOICE.pdf',
      },
    })
  })
)

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))

// Reset handlers after each test
beforeEach(() => server.resetHandlers())

// Clean up after all tests
afterAll(() => server.close())

describe('PDFViewer Integration Tests', () => {
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

    // Reset Zustand UI store to default state
    useUIStore.getState().resetPdfState()

    // Generate unique blob URL for each test to avoid mock caching
    const uniqueId = `${Date.now()}-${Math.random()}`
    global.URL.createObjectURL = () => `blob:mock-url-${uniqueId}`
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('should complete full PDF viewing workflow: load → navigate → zoom → search', async () => {
    // Arrange & Act - Load PDF
    render(<PDFViewer declarationId="test-decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    // Step 1: Wait for PDF to load (multiple pdf-document due to thumbnails)
    await waitFor(
      () => {
        const documents = screen.getAllByTestId('pdf-document')
        expect(documents.length).toBeGreaterThan(0)
      },
      { timeout: 5000 }
    )

    // Verify initial state
    expect(screen.getByDisplayValue('1')).toBeInTheDocument()
    expect(screen.getByText('/ 10')).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()

    // Step 2: Navigate to next page
    const nextButton = screen.getByTitle('Next Page')
    await user.click(nextButton)

    await waitFor(() => {
      expect(screen.getByDisplayValue('2')).toBeInTheDocument()
    })

    // Step 3: Zoom in
    const zoomInButton = screen.getByTitle('Zoom In')
    await user.click(zoomInButton)

    await waitFor(() => {
      expect(screen.getByText('125%')).toBeInTheDocument()
    })

    // Step 4: Search for text
    const searchInput = screen.getByPlaceholderText('Search in PDF...')
    await user.type(searchInput, 'invoice')

    // Wait for search results
    await waitFor(
      () => {
        expect(screen.getByText(/1 of/)).toBeInTheDocument()
      },
      { timeout: 5000 }
    )

    // Step 5: Navigate search results
    const nextMatchButton = screen.getByTitle('Next Match')
    expect(nextMatchButton).toBeInTheDocument()

    // Complete workflow success
    expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
  }, 10000) // Increase timeout for full workflow

  it('should switch between all document types', async () => {
    // Arrange
    render(<PDFViewer declarationId="test-decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
    })

    // Assert - All document tabs are visible
    expect(screen.getByText('Arrival Notice')).toBeInTheDocument()
    expect(screen.getByText('Bill of Lading')).toBeInTheDocument()
    expect(screen.getByText('C/O #1')).toBeInTheDocument()
    expect(screen.getByText('C/O #2')).toBeInTheDocument()
    expect(screen.getByText('Invoice')).toBeInTheDocument()

    // Act - Switch to Arrival Notice
    await user.click(screen.getByText('Arrival Notice'))

    // Wait for new PDF to load
    await waitFor(
      () => {
        expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
      },
      { timeout: 5000 }
    )

    // Act - Switch to Bill of Lading
    await user.click(screen.getByText('Bill of Lading'))

    await waitFor(
      () => {
        expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
      },
      { timeout: 5000 }
    )

    // Act - Switch to C/O #1
    await user.click(screen.getByText('C/O #1'))

    await waitFor(
      () => {
        expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
      },
      { timeout: 5000 }
    )

    // Success - All documents can be switched
    expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
  }, 15000)

  it('should render PDF within 3 seconds (performance requirement)', async () => {
    // Arrange - Measure real rendering time
    const startTime = performance.now()

    // Act - Render component
    render(<PDFViewer declarationId="test-decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    // Wait for PDF to load (should be fast with mocks)
    await waitFor(
      () => {
        expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
      },
      { timeout: 3000 }
    )

    const endTime = performance.now()
    const renderTime = endTime - startTime

    // Assert - Rendered within 3 seconds
    expect(renderTime).toBeLessThan(3000)
  })

  it('should handle missing file gracefully', async () => {
    // Arrange - Mock 404 error for INVOICE.pdf
    server.use(
      http.get(`${API_BASE_URL}/declarations/:id/files/INVOICE.pdf`, () => {
        return new HttpResponse(null, { status: 404 })
      })
    )

    // Act
    render(<PDFViewer declarationId="test-decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    // Assert - Error message displayed
    await waitFor(
      () => {
        expect(screen.getByText('Error loading PDF')).toBeInTheDocument()
      },
      { timeout: 5000 }
    )
  })

  it('should cache loaded PDFs and avoid redundant API calls', async () => {
    // Arrange - Track API calls
    let apiCallCount = 0
    server.use(
      http.get(
        `${API_BASE_URL}/declarations/:id/files/:filename`,
        ({ params }) => {
          apiCallCount++
          const { filename } = params
          const pdfContent = `Mock PDF content for ${filename}`
          return new HttpResponse(pdfContent, {
            status: 200,
            headers: {
              'Content-Type': 'application/pdf',
            },
          })
        }
      )
    )

    // Act - First render
    const { unmount } = render(
      <PDFViewer declarationId="test-decl-123" documentType="INVOICE" />,
      { wrapper }
    )

    await waitFor(() => {
      expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
    })

    const firstCallCount = apiCallCount

    // Act - Switch to another document
    await user.click(screen.getByText('Arrival Notice'))

    await waitFor(() => {
      expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
    })

    // Act - Switch back to Invoice (should use cache)
    await user.click(screen.getByText('Invoice'))

    await waitFor(() => {
      expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
    })

    // Assert - Invoice PDF should be cached (no additional API call)
    expect(apiCallCount).toBe(firstCallCount + 1) // Only AN.pdf fetched, Invoice cached

    unmount()
  })

  it('should handle thumbnail sidebar interactions', async () => {
    // Arrange
    render(<PDFViewer declarationId="test-decl-123" documentType="INVOICE" />, {
      wrapper,
    })

    await waitFor(() => {
      expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
    })

    // Assert - Sidebar visible by default
    expect(screen.getAllByText(/Page \d+/).length).toBeGreaterThan(1)

    // Act - Toggle sidebar off
    const toggleButton = screen.getByTitle('Toggle Sidebar')
    await user.click(toggleButton)

    // Assert - Sidebar hidden (only main viewer shows "Page X", thumbnails are hidden)
    await waitFor(() => {
      expect(screen.queryAllByText(/Page \d+/).length).toBe(1)
    })

    // Act - Toggle sidebar on
    await user.click(toggleButton)

    // Assert - Sidebar visible again
    await waitFor(() => {
      expect(screen.getAllByText(/Page \d+/).length).toBeGreaterThan(1)
    })
  })

  it('should handle highlight box navigation', async () => {
    // Arrange
    const highlightBox = {
      page: 5,
      bbox: [100, 150, 300, 100] as [number, number, number, number],
    }

    const { container } = render(
      <PDFViewer
        declarationId="test-decl-123"
        documentType="INVOICE"
        highlightBox={highlightBox}
      />,
      { wrapper }
    )

    // Wait for PDF to load
    await waitFor(() => {
      expect(screen.getAllByTestId('pdf-document').length).toBeGreaterThan(0)
    })

    // Assert - Auto-navigated to page 5
    await waitFor(() => {
      expect(screen.getByDisplayValue('5')).toBeInTheDocument()
    })

    // Assert - Highlight box overlay rendered
    const highlightOverlay = container.querySelector('.animate-pulse')
    expect(highlightOverlay).toBeInTheDocument()
    expect(highlightOverlay).toHaveClass('border-red-500')
  })
})
