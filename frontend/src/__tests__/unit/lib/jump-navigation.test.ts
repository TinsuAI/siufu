/**
 * Unit tests for Jump Navigation utilities (Story 3.7)
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { jumpToSource, hasSourceMetadata } from '@/lib/jump-navigation'
import type { SourceMetadataMap } from '@/lib/jump-navigation'
import { useUIStore } from '@/stores/ui-store'

// Mock Zustand store
vi.mock('@/stores/ui-store', () => ({
  useUIStore: {
    getState: vi.fn(),
    setState: vi.fn(),
    subscribe: vi.fn(),
  },
}))

describe('Jump Navigation Utils', () => {
  const mockSourceMetadata: SourceMetadataMap = {
    'company_info.importer_name': {
      source: 'INVOICE',
      page: 1,
      bbox: [0.1, 0.2, 0.3, 0.05],
    },
    'products.0.hs_code': {
      source: 'CO',
      page: 2,
      bbox: [0.5, 0.6, 0.2, 0.03],
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('hasSourceMetadata', () => {
    it('should return true if field has source metadata', () => {
      const result = hasSourceMetadata(
        'company_info.importer_name',
        mockSourceMetadata
      )
      expect(result).toBe(true)
    })

    it('should return false if field does not have source metadata', () => {
      const result = hasSourceMetadata(
        'tax_calculations.total_tax',
        mockSourceMetadata
      )
      expect(result).toBe(false)
    })

    it('should return false if sourceMetadata is null', () => {
      const result = hasSourceMetadata('company_info.importer_name', null)
      expect(result).toBe(false)
    })

    it('should return false if sourceMetadata is undefined', () => {
      const result = hasSourceMetadata('company_info.importer_name', undefined)
      expect(result).toBe(false)
    })
  })

  describe('jumpToSource', () => {
    it('should call setSourceHighlight with correct data', () => {
      const mockSetSourceHighlight = vi.fn()
      const mockSetActiveDocumentTab = vi.fn()

      vi.mocked(useUIStore.getState).mockReturnValue({
        setSourceHighlight: mockSetSourceHighlight,
        setActiveDocumentTab: mockSetActiveDocumentTab,
      } as any)

      jumpToSource('company_info.importer_name', mockSourceMetadata)

      expect(mockSetActiveDocumentTab).toHaveBeenCalledWith('INVOICE')
      expect(mockSetSourceHighlight).toHaveBeenCalledWith({
        documentType: 'INVOICE',
        page: 1,
        bbox: [0.1, 0.2, 0.3, 0.05],
        timestamp: expect.any(Number),
      })
    })

    it('should warn if field has no source metadata', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const mockSetSourceHighlight = vi.fn()
      const mockSetActiveDocumentTab = vi.fn()

      vi.mocked(useUIStore.getState).mockReturnValue({
        setSourceHighlight: mockSetSourceHighlight,
        setActiveDocumentTab: mockSetActiveDocumentTab,
      } as any)

      jumpToSource('tax_calculations.total_tax', mockSourceMetadata)

      expect(consoleSpy).toHaveBeenCalledWith(
        'No source metadata found for field: tax_calculations.total_tax'
      )
      expect(mockSetSourceHighlight).not.toHaveBeenCalled()
      expect(mockSetActiveDocumentTab).not.toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('should handle different document types', () => {
      const mockSetSourceHighlight = vi.fn()
      const mockSetActiveDocumentTab = vi.fn()

      vi.mocked(useUIStore.getState).mockReturnValue({
        setSourceHighlight: mockSetSourceHighlight,
        setActiveDocumentTab: mockSetActiveDocumentTab,
      } as any)

      jumpToSource('products.0.hs_code', mockSourceMetadata)

      expect(mockSetActiveDocumentTab).toHaveBeenCalledWith('CO')
      expect(mockSetSourceHighlight).toHaveBeenCalledWith({
        documentType: 'CO',
        page: 2,
        bbox: [0.5, 0.6, 0.2, 0.03],
        timestamp: expect.any(Number),
      })
    })
  })
})
