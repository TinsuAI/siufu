/**
 * Declaration Status Enum
 * Matches backend DeclarationStatus enum values
 */
export enum DeclarationStatus {
  UPLOADED = 'UPLOADED',
  PROCESSING = 'PROCESSING',
  VALIDATING = 'VALIDATING',
  READY_FOR_REVIEW = 'READY_FOR_REVIEW',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  FAILED = 'FAILED',
}

/**
 * Processing Stage Enum
 * Frontend-only enum for visual progress display
 * Maps to backend DeclarationStatus with progress percentage
 */
export enum ProcessingStage {
  UPLOADING = 'UPLOADING',
  OCR_PROCESSING = 'OCR_PROCESSING',
  AI_EXTRACTION = 'AI_EXTRACTION',
  VALIDATING = 'VALIDATING',
  GENERATING_EXCEL = 'GENERATING_EXCEL',
  READY_FOR_REVIEW = 'READY_FOR_REVIEW',
}

/**
 * Stage labels for display
 */
export const STAGE_LABELS: Record<ProcessingStage, string> = {
  [ProcessingStage.UPLOADING]: 'Uploading',
  [ProcessingStage.OCR_PROCESSING]: 'OCR Processing',
  [ProcessingStage.AI_EXTRACTION]: 'AI Extraction',
  [ProcessingStage.VALIDATING]: 'Validation',
  [ProcessingStage.GENERATING_EXCEL]: 'Generating Excel',
  [ProcessingStage.READY_FOR_REVIEW]: 'Ready for Review',
}

/**
 * Map backend status + progress to frontend ProcessingStage
 * @param status Backend DeclarationStatus
 * @param progress Processing progress (0.0 to 1.0)
 * @returns Corresponding ProcessingStage
 */
export function mapStatusToStage(
  status: DeclarationStatus,
  progress: number
): ProcessingStage {
  switch (status) {
    case DeclarationStatus.UPLOADED:
      return ProcessingStage.UPLOADING

    case DeclarationStatus.PROCESSING:
      if (progress < 0.3) {
        return ProcessingStage.OCR_PROCESSING
      } else if (progress < 0.7) {
        return ProcessingStage.AI_EXTRACTION
      } else {
        return ProcessingStage.VALIDATING
      }

    case DeclarationStatus.VALIDATING:
      if (progress > 0.9) {
        return ProcessingStage.GENERATING_EXCEL
      } else {
        return ProcessingStage.VALIDATING
      }

    case DeclarationStatus.READY_FOR_REVIEW:
    case DeclarationStatus.APPROVED:
    case DeclarationStatus.REJECTED:
      return ProcessingStage.READY_FOR_REVIEW

    case DeclarationStatus.FAILED:
      // Return the last stage before failure
      return ProcessingStage.AI_EXTRACTION

    default:
      return ProcessingStage.UPLOADING
  }
}

/**
 * Processing Log Entry
 * Single log entry for monitoring processing activity
 */
export interface ProcessingLogEntry {
  timestamp: string
  level: 'info' | 'success' | 'warning' | 'error'
  message: string
  details?: Record<string, any>
}

/**
 * Status Response from GET /api/declarations/{id}/status
 */
export interface StatusResponse {
  id: string
  status: DeclarationStatus
  processing_progress: number // 0.0 to 1.0
  processing_error: string | null
  processing_log: ProcessingLogEntry[]
  created_at: string // ISO 8601 timestamp
  updated_at: string // ISO 8601 timestamp
}

/**
 * Retry Processing Response from POST /api/declarations/{id}/process
 */
export interface RetryProcessingResponse {
  message: string
  declaration_id: string
}

/**
 * Check if status is a terminal state (polling should stop)
 */
export function isTerminalStatus(status: DeclarationStatus): boolean {
  return [
    DeclarationStatus.READY_FOR_REVIEW,
    DeclarationStatus.APPROVED,
    DeclarationStatus.REJECTED,
    DeclarationStatus.FAILED,
  ].includes(status)
}

/**
 * Check if status is actively processing (polling should continue)
 */
export function isProcessingStatus(status: DeclarationStatus): boolean {
  return [
    DeclarationStatus.UPLOADED,
    DeclarationStatus.PROCESSING,
    DeclarationStatus.VALIDATING,
  ].includes(status)
}

/**
 * Document Type Enum for PDF Viewer
 * Represents the four types of source documents in a declaration
 */
export type DocumentType = 'AN' | 'BOL' | 'CO' | 'INVOICE'

/**
 * Highlight Box Interface for Jump-to-Source Feature
 * Defines a rectangular region on a PDF page to highlight
 * Coordinates are in PDF points (1/72 inch), origin is top-left
 */
export interface HighlightBox {
  page: number // Page number (1-indexed)
  bbox: [number, number, number, number] // [x, y, width, height]
}

/**
 * PDF Viewer Component Props
 * Used by the PDFViewer component to display source documents
 */
export interface PDFViewerProps {
  declarationId: string // Declaration UUID
  documentType: DocumentType // Which document to display
  highlightBox?: HighlightBox // Optional highlight region for jump-to-source
}

/**
 * Uploaded File Interface
 * Represents a file uploaded as part of a declaration
 */
export interface UploadedFile {
  filename: string
  file_type: string
  upload_timestamp: string
}

/**
 * Validation Warning Interface
 * Represents a validation issue found during declaration processing
 */
export interface ValidationWarning {
  message: string
  severity: 'error' | 'warning'
  field?: string // Optional field reference
}

/**
 * Product Line Item in Draft Data
 */
export interface ProductLineItem {
  description: string
  hs_code: string
  quantity: number
  unit: string
  unit_price: number
  total_price: number
  origin_country: string
}

/**
 * Draft Data Structure (User-Editable Declaration Data)
 * Stored in JSONB field, flexible schema
 */
export interface DraftData {
  // Company Information
  company_info: {
    importer_name: string
    tax_id: string
    address: string
    city: string
    country: string
    contact_person: string
    contact_email: string
    contact_phone: string
  }
  // Shipment Details
  shipment_details: {
    bol_number: string
    arrival_date: string
    port_of_arrival: string
    port_of_departure: string
    container_numbers: string[]
    vessel_name: string
  }
  // Product Line Items
  products: ProductLineItem[]
  // Tax Calculations
  tax_calculations: {
    subtotal: number
    vat_rate: number
    vat_amount: number
    import_duty_rate: number
    import_duty_amount: number
    total_tax: number
    grand_total: number
  }
}

/**
 * Source Metadata for Jump Navigation (Story 3.7)
 * Maps field paths to their source document locations
 */
export interface FieldSourceMetadata {
  source: DocumentType
  page: number
  bbox: [number, number, number, number] // [x, y, width, height] normalized 0-1
}

/**
 * Full Declaration Interface
 * Represents a complete declaration with all metadata and processing state
 */
export interface Declaration {
  id: string
  status: DeclarationStatus
  uploaded_files: UploadedFile[]
  extracted_data: Record<string, unknown> | null
  draft_data: DraftData | null // This is what the form edits
  validation_warnings: ValidationWarning[]
  confidence_scores: Record<string, number> // e.g., {"company_info.importer_name": 0.95}
  source_metadata: Record<string, FieldSourceMetadata> | null // Story 3.7: field_path -> {source, page, bbox}
  processing_progress: number
  processing_error: string | null
  created_at: string
  updated_at: string
  user_id: string
}

/**
 * Declaration List Item (Story 3.9)
 * Optimized schema for list view - excludes large fields for performance
 */
export interface DeclarationListItem {
  id: string
  status: DeclarationStatus
  created_at: string
  updated_at: string
  approved_at: string | null
  products_count: number
}

/**
 * Declaration List Response (Story 3.9)
 * Paginated response for declaration list endpoint
 */
export interface DeclarationListResponse {
  items: DeclarationListItem[]
  total: number
  page: number
  limit: number
  total_pages: number
}

/**
 * Declaration List Query Params (Story 3.9)
 * Query parameters for filtering and sorting declarations
 */
export interface DeclarationListParams {
  page?: number
  limit?: number
  status?: string
  search?: string
  sort_by?: 'created_at' | 'status'
  sort_order?: 'asc' | 'desc'
}
