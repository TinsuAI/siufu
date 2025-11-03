'use client'

import { useState, useMemo } from 'react'
import { Document, Page } from 'react-pdf'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize,
  PanelLeft,
  Search,
  X,
} from 'lucide-react'
import { usePDFDocument } from '@/hooks/use-pdf-document'
import { useUIStore } from '@/stores/ui-store'
import type { PDFViewerProps } from '@/types/declaration'
import { DocumentTabs } from './document-tabs'

// Import react-pdf styles
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

/**
 * PDF Viewer Component
 * Displays PDF documents with navigation, zoom, and thumbnail sidebar
 */
export function PDFViewer({
  declarationId,
  documentType,
  highlightBox,
}: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageInputValue, setPageInputValue] = useState<string>('1')
  const [currentFilename, setCurrentFilename] = useState<string>('')

  // Search state
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [searchResults, setSearchResults] = useState<
    Array<{ page: number; text: string }>
  >([])
  const [currentSearchIndex, setCurrentSearchIndex] = useState<number>(0)
  const [pdfTextContent, setPdfTextContent] = useState<Map<number, string>>(
    new Map()
  )

  // Get PDF state from Zustand store
  const {
    pdfZoom,
    pdfCurrentPage,
    thumbnailSidebarOpen,
    setPdfZoom,
    setPdfCurrentPage,
    toggleThumbnailSidebar,
  } = useUIStore()

  // Fetch PDF using TanStack Query (use currentFilename if set, otherwise fallback to documentType)
  const filename =
    currentFilename ||
    (() => {
      const fileMap = {
        AN: 'AN.pdf',
        BOL: 'BOL.pdf',
        CO: 'CO.pdf',
        INVOICE: 'INVOICE.pdf',
      }
      return fileMap[documentType] || 'INVOICE.pdf'
    })()

  const {
    data: pdfBlob,
    isLoading,
    error,
  } = usePDFDocument(declarationId, filename)

  // Handle document tab change
  const handleDocumentChange = (newFilename: string) => {
    setCurrentFilename(newFilename)
    // Reset search when changing documents
    setSearchQuery('')
    setSearchResults([])
    setCurrentSearchIndex(0)
    setPdfTextContent(new Map())
  }

  // Convert Blob to URL for react-pdf
  const pdfUrl = useMemo(() => {
    if (!pdfBlob) return null
    return URL.createObjectURL(pdfBlob)
  }, [pdfBlob])

  // Cleanup object URL when component unmounts
  useMemo(() => {
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl)
      }
    }
  }, [pdfUrl])

  // PDF loaded successfully
  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setPdfCurrentPage(1) // Reset to first page when new document loads
    setPageInputValue('1')

    // Auto-navigate to highlight box if provided
    if (highlightBox) {
      setPdfCurrentPage(highlightBox.page)
      setPageInputValue(highlightBox.page.toString())
    }
  }

  // Handle page navigation
  const goToPreviousPage = () => {
    if (pdfCurrentPage > 1) {
      const newPage = pdfCurrentPage - 1
      setPdfCurrentPage(newPage)
      setPageInputValue(newPage.toString())
    }
  }

  const goToNextPage = () => {
    if (pdfCurrentPage < numPages) {
      const newPage = pdfCurrentPage + 1
      setPdfCurrentPage(newPage)
      setPageInputValue(newPage.toString())
    }
  }

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPageInputValue(e.target.value)
  }

  const handlePageInputBlur = () => {
    const pageNum = parseInt(pageInputValue, 10)
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= numPages) {
      setPdfCurrentPage(pageNum)
    } else {
      setPageInputValue(pdfCurrentPage.toString())
    }
  }

  const handlePageInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handlePageInputBlur()
    }
  }

  // Handle zoom controls
  const handleZoomIn = () => {
    setPdfZoom(Math.min(pdfZoom + 0.25, 3.0)) // Max zoom 300%
  }

  const handleZoomOut = () => {
    setPdfZoom(Math.max(pdfZoom - 0.25, 0.5)) // Min zoom 50%
  }

  const handleFitToWidth = () => {
    setPdfZoom(1.0) // Reset to 100%
  }

  const handleFitToPage = () => {
    setPdfZoom(0.8) // 80% to fit page with margin
  }

  // Handle thumbnail click
  const handleThumbnailClick = (pageNum: number) => {
    setPdfCurrentPage(pageNum)
    setPageInputValue(pageNum.toString())
  }

  // Handle search
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value
    setSearchQuery(query)

    if (!query.trim()) {
      setSearchResults([])
      setCurrentSearchIndex(0)
      return
    }

    // Search through all page text content
    const results: Array<{ page: number; text: string }> = []
    const lowerQuery = query.toLowerCase()

    pdfTextContent.forEach((text, page) => {
      if (text.toLowerCase().includes(lowerQuery)) {
        results.push({ page, text })
      }
    })

    setSearchResults(results)
    setCurrentSearchIndex(0)

    // Navigate to first result
    if (results.length > 0) {
      setPdfCurrentPage(results[0].page)
      setPageInputValue(results[0].page.toString())
    }
  }

  const handleSearchClear = () => {
    setSearchQuery('')
    setSearchResults([])
    setCurrentSearchIndex(0)
  }

  const handlePreviousMatch = () => {
    if (searchResults.length === 0) return

    const newIndex =
      currentSearchIndex === 0
        ? searchResults.length - 1
        : currentSearchIndex - 1
    setCurrentSearchIndex(newIndex)
    setPdfCurrentPage(searchResults[newIndex].page)
    setPageInputValue(searchResults[newIndex].page.toString())
  }

  const handleNextMatch = () => {
    if (searchResults.length === 0) return

    const newIndex = (currentSearchIndex + 1) % searchResults.length
    setCurrentSearchIndex(newIndex)
    setPdfCurrentPage(searchResults[newIndex].page)
    setPageInputValue(searchResults[newIndex].page.toString())
  }

  // Extract text content from PDF on page render
  const handlePageLoadSuccess = async (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    page: any
  ) => {
    try {
      const textContent = await page.getTextContent()
      const pageText = textContent.items
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((item: any) => item.str)
        .join(' ')

      setPdfTextContent((prev) => {
        const newMap = new Map(prev)
        newMap.set(page.pageNumber, pageText)
        return newMap
      })
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error extracting text from page:', error)
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <Card className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading PDF...</p>
        </div>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <p className="text-sm font-semibold text-destructive">
            Error loading PDF
          </p>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </Card>
    )
  }

  // No PDF data
  if (!pdfUrl) {
    return (
      <Card className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">No PDF available</p>
      </Card>
    )
  }

  return (
    <div className="flex h-full gap-4">
      {/* Thumbnail Sidebar */}
      {thumbnailSidebarOpen && (
        <Card className="w-48 p-4">
          <ScrollArea className="h-full">
            <div className="flex flex-col gap-2">
              {Array.from({ length: numPages }, (_, i) => i + 1).map(
                (pageNum) => (
                  <button
                    key={pageNum}
                    onClick={() => handleThumbnailClick(pageNum)}
                    className={`relative cursor-pointer rounded border-2 transition-colors ${
                      pageNum === pdfCurrentPage
                        ? 'border-primary'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <Document file={pdfUrl} loading="">
                      <Page
                        pageNumber={pageNum}
                        width={160}
                        renderAnnotationLayer={false}
                        renderTextLayer={false}
                      />
                    </Document>
                    <div className="mt-1 text-center text-xs text-muted-foreground">
                      Page {pageNum}
                    </div>
                  </button>
                )
              )}
            </div>
          </ScrollArea>
        </Card>
      )}

      {/* Main PDF Viewer */}
      <div className="flex flex-1 flex-col">
        {/* Document Tabs */}
        <div className="mb-4">
          <DocumentTabs
            declarationId={declarationId}
            onDocumentChange={handleDocumentChange}
          />
        </div>

        {/* Toolbar */}
        <Card className="mb-4 flex items-center gap-2 p-2">
          {/* Sidebar Toggle */}
          <Button
            variant="outline"
            size="icon"
            onClick={toggleThumbnailSidebar}
            title="Toggle Sidebar"
          >
            <PanelLeft className="h-4 w-4" />
          </Button>

          <div className="h-6 w-px bg-border" />

          {/* Page Navigation */}
          <Button
            variant="outline"
            size="icon"
            onClick={goToPreviousPage}
            disabled={pdfCurrentPage <= 1}
            title="Previous Page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          <div className="flex items-center gap-1">
            <Input
              type="text"
              value={pageInputValue}
              onChange={handlePageInputChange}
              onBlur={handlePageInputBlur}
              onKeyDown={handlePageInputKeyDown}
              className="w-16 text-center"
            />
            <span className="text-sm text-muted-foreground">/ {numPages}</span>
          </div>

          <Button
            variant="outline"
            size="icon"
            onClick={goToNextPage}
            disabled={pdfCurrentPage >= numPages}
            title="Next Page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          <div className="h-6 w-px bg-border" />

          {/* Zoom Controls */}
          <Button
            variant="outline"
            size="icon"
            onClick={handleZoomOut}
            title="Zoom Out"
          >
            <ZoomOut className="h-4 w-4" />
          </Button>

          <span className="w-16 text-center text-sm">
            {Math.round(pdfZoom * 100)}%
          </span>

          <Button
            variant="outline"
            size="icon"
            onClick={handleZoomIn}
            title="Zoom In"
          >
            <ZoomIn className="h-4 w-4" />
          </Button>

          <Button variant="outline" size="sm" onClick={handleFitToWidth}>
            Fit Width
          </Button>

          <Button variant="outline" size="sm" onClick={handleFitToPage}>
            <Maximize className="mr-2 h-4 w-4" />
            Fit Page
          </Button>

          <div className="h-6 w-px bg-border" />

          {/* Search Controls */}
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search in PDF..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-48"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleSearchClear}
                title="Clear Search"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {searchResults.length > 0 && (
            <>
              <span className="text-sm text-muted-foreground">
                {currentSearchIndex + 1} of {searchResults.length}
              </span>
              <Button
                variant="outline"
                size="icon"
                onClick={handlePreviousMatch}
                title="Previous Match"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={handleNextMatch}
                title="Next Match"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </>
          )}
        </Card>

        {/* PDF Canvas */}
        <Card className="flex-1 overflow-auto">
          <ScrollArea className="h-full">
            <div className="flex justify-center p-4">
              <Document
                file={pdfUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={
                  <div className="flex items-center justify-center p-8">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                  </div>
                }
                error={
                  <div className="p-8 text-center text-destructive">
                    Failed to load PDF document
                  </div>
                }
              >
                <div className="relative">
                  <Page
                    pageNumber={pdfCurrentPage}
                    scale={pdfZoom}
                    onLoadSuccess={handlePageLoadSuccess}
                    loading={
                      <div className="flex h-96 items-center justify-center">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                      </div>
                    }
                  />
                  {/* Highlight Box Overlay (Task 8) */}
                  {highlightBox && highlightBox.page === pdfCurrentPage && (
                    <div
                      className="absolute animate-pulse border-2 border-red-500 bg-red-500/20"
                      style={{
                        left: `${highlightBox.bbox[0] * pdfZoom}px`,
                        top: `${highlightBox.bbox[1] * pdfZoom}px`,
                        width: `${highlightBox.bbox[2] * pdfZoom}px`,
                        height: `${highlightBox.bbox[3] * pdfZoom}px`,
                      }}
                    />
                  )}
                </div>
              </Document>
            </div>
          </ScrollArea>
        </Card>
      </div>
    </div>
  )
}
