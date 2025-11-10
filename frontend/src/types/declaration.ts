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
  details?: Record<string, unknown>
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
  severity: 'error' | 'warning' | 'info'
  field?: string // Optional field reference
  rule?: string // Rule identifier (e.g., "quantity_mismatch", "amount_discrepancy")
  details?: {
    source_docs?: string[] // Documents involved (e.g., ["INVOICE", "CO"])
    expected_value?: any // Expected value
    actual_value?: any // Actual value found
    confidence?: number // Confidence score (0.0-1.0)
  }
}

/**
 * Product Line Item in Draft Data (18 fields per product)
 * Matches backend ProductLineItem schema
 */
export interface ProductLineItem {
  item_number?: number | null
  hs_code?: string | null
  product_description?: string | null
  quantity_1?: number | null
  quantity_unit_1?: string | null
  quantity_2?: number | null
  quantity_unit_2?: string | null
  invoice_unit_price?: number | null
  invoice_unit_price_currency?: string | null
  invoice_line_total?: number | null
  taxable_value_vnd?: number | null
  unit_price_vnd?: number | null
  country_of_origin_code?: string | null
  country_of_origin_name?: string | null
  preferential_code?: string | null
  manufacturer_name?: string | null
  brand_name?: string | null
  condition?: string | null
}

/**
 * Declaration Header (6 fields)
 */
export interface DeclarationHeader {
  declaration_number?: string | null
  declaration_type_code?: string | null
  customs_office_code?: string | null
  processing_division_code?: string | null
  registration_date?: string | null
  representative_hs_code?: string | null
}

/**
 * Importer Information (5 fields)
 */
export interface Importer {
  tax_code?: string | null
  name?: string | null
  postal_code?: string | null
  address?: string | null
  phone?: string | null
}

/**
 * Exporter Information (5 fields)
 */
export interface Exporter {
  name?: string | null
  address_line1?: string | null
  address_line2?: string | null
  address_line3?: string | null
  country_code?: string | null
}

/**
 * Shipping & Transport Information (10 fields)
 */
export interface ShippingTransport {
  bill_of_lading_number?: string | null
  warehouse_code?: string | null
  warehouse_name?: string | null
  port_of_discharge_code?: string | null
  port_of_discharge_name?: string | null
  port_of_loading_code?: string | null
  port_of_loading_name?: string | null
  transport_mode_code?: string | null
  vessel_name?: string | null
  arrival_date?: string | null
}

/**
 * Package & Container Information (6 fields)
 */
export interface PackageContainer {
  total_packages?: number | null
  package_unit?: string | null
  package_marks?: string | null
  gross_weight_kg?: number | null
  gross_weight_unit?: string | null
  container_count?: number | null
}

/**
 * Invoice Information (8 fields)
 */
export interface Invoice {
  invoice_number?: string | null
  invoice_date?: string | null
  payment_method_code?: string | null
  invoice_total?: number | null
  invoice_currency?: string | null
  invoice_incoterm?: string | null
  total_taxable_value_vnd?: number | null
  exchange_rate?: number | null
}

/**
 * Certificate of Origin (3 fields)
 */
export interface CertificateOfOrigin {
  co_form_type?: string | null
  co_number?: string | null
  co_date?: string | null
}

/**
 * Import Duty (4 fields)
 */
export interface ImportDuty {
  rate?: number | null
  rate_type?: string | null
  amount?: number | null
  exemption_amount?: number | null
}

/**
 * VAT & Other Taxes (6 fields)
 */
export interface VAT {
  name?: string | null
  rate_code?: string | null
  rate?: number | null
  taxable_value_vnd?: number | null
  amount?: number | null
  exemption_amount?: number | null
}

/**
 * Tax Summary (4 fields)
 */
export interface TaxSummary {
  total_tax_amount_vnd?: number | null
  tax_payment_deadline_code?: string | null
  taxpayer_type?: string | null
  tax_classification?: string | null
}

/**
 * Metadata (2 fields - read-only)
 */
export interface Metadata {
  total_pages?: number | null
  total_line_items?: number | null
}

/**
 * Draft Data Structure (User-Editable Declaration Data - 77 fields total)
 * Matches backend VietnameseDeclarationData schema
 * Stored in JSONB field, flexible schema
 */
export interface DraftData {
  declaration_header?: DeclarationHeader
  importer?: Importer
  exporter?: Exporter
  shipping_transport?: ShippingTransport
  package_container?: PackageContainer
  invoice?: Invoice
  certificate_of_origin?: CertificateOfOrigin
  products?: ProductLineItem[]
  import_duty?: ImportDuty
  vat?: VAT
  tax_summary?: TaxSummary
  metadata?: Metadata
}

/**
 * Legacy Draft Data Structure (DEPRECATED - for backward compatibility)
 * Old 25-field structure - will be removed in future versions
 */
export interface LegacyDraftData {
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
  products: Array<{
    description: string
    hs_code: string
    quantity: number
    unit: string
    unit_price: number
    total_price: number
    origin_country: string
  }>
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

export interface LinkedCompanySummary {
  id: string
  name: string
  is_verified: boolean
  declaration_count: number
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
  importer_id: string | null
  exporter_id: string | null
  importer_summary: LinkedCompanySummary | null
  exporter_summary: LinkedCompanySummary | null
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

/**
 * Correction Category (Story 3.6 Expansion)
 * Categories for user corrections to help improve AI
 */
export type CorrectionCategory =
  | 'AI Extraction Error'
  | 'Wrong HS Code'
  | 'Calculation Error'
  | 'Missing Data'
  | 'Format Issue'
  | 'Other'

/**
 * Correction Create Request (Story 3.6 Expansion)
 * Payload for creating a new correction flag
 */
export interface CorrectionCreate {
  field_name: string
  original_value: string | null
  corrected_value: string
  correction_category: CorrectionCategory
  expected_value: string // Required: What the correct value should be
  notes: string // Required: Explanation of why this is wrong
  screenshots?: string[] // Optional: URLs of uploaded screenshot images
}

/**
 * Correction Response (Story 3.6 Expansion)
 * Single correction record from backend
 */
export interface CorrectionResponse {
  id: string
  declaration_id: string
  field_name: string
  original_value: string | null
  corrected_value: string
  correction_category: CorrectionCategory
  expected_value: string // Required: What the correct value should be
  notes: string // Required: Explanation of why this is wrong
  screenshots: string[] | null // Optional: URLs of screenshot images
  user_id: string
  user_name: string
  created_at: string
}

/**
 * Correction List Response (Story 3.6 Expansion)
 * List of corrections for a declaration
 */
export interface CorrectionListResponse {
  corrections: CorrectionResponse[]
  count: number
}
