import { create } from 'zustand'
import type { DocumentType } from '@/types/declaration'

/**
 * UI Store for client-side UI preferences
 * Stores PDF viewer controls (zoom, page, active tab, sidebar visibility)
 */
interface UIState {
  // PDF Viewer State
  pdfZoom: number // Zoom level (1.0 = 100%, 1.5 = 150%)
  pdfCurrentPage: number // Current page number (1-indexed)
  activeDocumentTab: DocumentType // Which PDF document is currently displayed
  thumbnailSidebarOpen: boolean // Thumbnail sidebar visibility

  // PDF Viewer Actions
  setPdfZoom: (zoom: number) => void
  setPdfCurrentPage: (page: number) => void
  setActiveDocumentTab: (tab: DocumentType) => void
  toggleThumbnailSidebar: () => void
  resetPdfState: () => void // Reset PDF state to defaults
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

  // Actions
  setPdfZoom: (zoom: number) => set({ pdfZoom: zoom }),
  setPdfCurrentPage: (page: number) => set({ pdfCurrentPage: page }),
  setActiveDocumentTab: (tab: DocumentType) =>
    set({ activeDocumentTab: tab, pdfCurrentPage: 1 }), // Reset page when switching documents
  toggleThumbnailSidebar: () =>
    set((state) => ({ thumbnailSidebarOpen: !state.thumbnailSidebarOpen })),
  resetPdfState: () =>
    set({
      pdfZoom: 1.0,
      pdfCurrentPage: 1,
      activeDocumentTab: 'INVOICE',
      thumbnailSidebarOpen: true,
    }),
}))
