/**
 * Jump Navigation Utility (Story 3.7)
 *
 * Utilities for jumping to source document locations when user clicks field labels
 */
import type { DocumentType } from '@/types/declaration'
import { useUIStore } from '@/stores/ui-store'

/**
 * Source metadata for a single field
 */
export interface FieldSourceMetadata {
  source: DocumentType
  page: number
  bbox: [number, number, number, number] // [x, y, width, height] normalized 0-1
}

/**
 * Source metadata mapping: field_path -> source location
 */
export type SourceMetadataMap = Record<string, FieldSourceMetadata>

/**
 * Jump to source location for a field
 *
 * Updates Zustand store to highlight the source location in PDF viewer
 *
 * @param fieldPath - Dot-notation field path (e.g., "company_info.importer_name")
 * @param sourceMetadata - Full source metadata map from API
 */
export function jumpToSource(
  fieldPath: string,
  sourceMetadata: SourceMetadataMap
): void {
  const fieldMeta = sourceMetadata[fieldPath]

  if (!fieldMeta) {
    // eslint-disable-next-line no-console
    console.warn(`No source metadata found for field: ${fieldPath}`)
    return
  }

  const { source, page, bbox } = fieldMeta

  // Set highlight in UI store with auto-clear after 3s
  const { setSourceHighlight, setActiveDocumentTab } = useUIStore.getState()

  // Switch to correct document tab
  setActiveDocumentTab(source)

  // Set highlight with timestamp for auto-clear
  setSourceHighlight({
    documentType: source,
    page,
    bbox,
    timestamp: Date.now(),
  })
}

/**
 * Check if a field has source metadata
 *
 * @param fieldPath - Dot-notation field path
 * @param sourceMetadata - Full source metadata map
 * @returns true if field has source metadata
 */
export function hasSourceMetadata(
  fieldPath: string,
  sourceMetadata: SourceMetadataMap | null | undefined
): boolean {
  if (!sourceMetadata) return false
  return fieldPath in sourceMetadata
}
