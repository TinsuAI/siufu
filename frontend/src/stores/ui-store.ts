import { create } from 'zustand'
import type { DocumentType } from '@/types/declaration'

export type DocumentTabType = DocumentType | `CO_${number}`

/**
 * Source highlight for jump navigation (Story 3.7)
 */
export interface SourceHighlight {
  documentType: DocumentType
  page: number
  bbox: [number, number, number, number] // [x, y, width, height] normalized 0-1
  timestamp: number // For auto-clear logic
}

/**
 * UI Store for client-side UI preferences
 * Stores PDF viewer controls (zoom, page, active tab, sidebar visibility)
 * Story 3.7: Added sourceHighlight for jump navigation
 */
export interface UIState {
  // PDF Viewer State
  pdfZoom: number // Zoom level (1.0 = 100%, 1.5 = 150%)
  pdfCurrentPage: number // Current page number (1-indexed)
  activeDocumentTab: DocumentTabType // Which PDF document is currently displayed
  thumbnailSidebarOpen: boolean // Thumbnail sidebar visibility

  // Jump Navigation State (Story 3.7)
  sourceHighlight: SourceHighlight | null // Current highlight to display

  // PDF Viewer Actions
  setPdfZoom: (zoom: number) => void
  setPdfCurrentPage: (page: number) => void
  setActiveDocumentTab: (tab: DocumentTabType) => void
  toggleThumbnailSidebar: () => void
  resetPdfState: () => void // Reset PDF state to defaults

  // Jump Navigation Actions (Story 3.7)
  setSourceHighlight: (highlight: SourceHighlight | null) => void
}

/**
 * Create UI store with Zustand
 */
export const useUIStore = create<UIState>((set) => ({
  // Default state
  pdfZoom: 1.0,
  pdfCurrentPage: 1,
  activeDocumentTab: 'INVOICE', // Default to Invoice document
  thumbnailSidebarOpen: true,
  sourceHighlight: null, // Story 3.7

  // Actions
  setPdfZoom: (zoom: number) => set({ pdfZoom: zoom }),
  setPdfCurrentPage: (page: number) => set({ pdfCurrentPage: page }),
  setActiveDocumentTab: (tab: DocumentTabType) =>
    set({ activeDocumentTab: tab, pdfCurrentPage: 1 }), // Reset page when switching documents
  toggleThumbnailSidebar: () =>
    set((state) => ({ thumbnailSidebarOpen: !state.thumbnailSidebarOpen })),
  resetPdfState: () =>
    set({
      pdfZoom: 1.0,
      pdfCurrentPage: 1,
      activeDocumentTab: 'INVOICE',
      thumbnailSidebarOpen: true,
      sourceHighlight: null,
    }),

  // Story 3.7: Jump Navigation Actions
  setSourceHighlight: (highlight: SourceHighlight | null) => {
    set({ sourceHighlight: highlight })

    // Auto-clear highlight after 3 seconds
    if (highlight !== null) {
      setTimeout(() => {
        set((state) => {
          // Only clear if this is still the same highlight (timestamp match)
          if (state.sourceHighlight?.timestamp === highlight.timestamp) {
            return { sourceHighlight: null }
          }
          return state
        })
      }, 3000)
    }
  },
}))
