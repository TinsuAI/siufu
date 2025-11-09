/**
 * Company master data types for importers and exporters
 * Generated from backend OpenAPI schemas
 */

// ============================================================================
// Importer Types
// ============================================================================

export interface ImporterBase {
  tax_code: string
  name: string
  postal_code?: string | null
  address?: string | null
  phone?: string | null
}

export type ImporterCreate = ImporterBase

export interface ImporterUpdate {
  tax_code?: string
  name?: string
  postal_code?: string | null
  address?: string | null
  phone?: string | null
}

export interface ImporterDetail extends ImporterBase {
  id: string
  name_normalized: string

  // Metadata
  organization_id: string
  first_seen_declaration_id?: string | null
  last_seen_declaration_id?: string | null
  declaration_count: number

  // Quality tracking
  is_verified: boolean
  confidence_score: number
  last_reviewed_by_user_id?: string | null
  last_reviewed_at?: string | null

  // Audit
  created_at: string
  updated_at: string
  deleted_at?: string | null
}

export interface ImporterListItem {
  id: string
  tax_code: string
  name: string
  declaration_count: number
  is_verified: boolean
  last_seen_declaration_id?: string | null
  updated_at: string
}

// ============================================================================
// Exporter Types
// ============================================================================

export interface ExporterBase {
  name: string
  country_code: string
  address_line1?: string | null
  address_line2?: string | null
  address_line3?: string | null
}

export type ExporterCreate = ExporterBase

export interface ExporterUpdate {
  name?: string
  country_code?: string
  address_line1?: string | null
  address_line2?: string | null
  address_line3?: string | null
}

export interface ExporterDetail extends ExporterBase {
  id: string
  name_normalized: string

  // Metadata
  organization_id: string
  first_seen_declaration_id?: string | null
  last_seen_declaration_id?: string | null
  declaration_count: number

  // Quality tracking
  is_verified: boolean
  confidence_score: number
  last_reviewed_by_user_id?: string | null
  last_reviewed_at?: string | null

  // Audit
  created_at: string
  updated_at: string
  deleted_at?: string | null
}

export interface ExporterListItem {
  id: string
  name: string
  country_code: string
  declaration_count: number
  is_verified: boolean
  last_seen_declaration_id?: string | null
  updated_at: string
}

// ============================================================================
// Shared Company Types
// ============================================================================

export type CompanyType = 'importers' | 'exporters'

export type CompanyDetail = ImporterDetail | ExporterDetail
export type CompanyListItem = ImporterListItem | ExporterListItem
export type CompanyCreate = ImporterCreate | ExporterCreate
export type CompanyUpdate = ImporterUpdate | ExporterUpdate

export interface CompanyListResponse<T = CompanyListItem> {
  items: T[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface DuplicatePair<T = CompanyListItem> {
  company1: T
  company2: T
  similarity: number
  reason: string
}

export interface MergeRequest {
  keep_id: string
  merge_id: string
}

// ============================================================================
// Query Parameters
// ============================================================================

export type CompanyFilterType = 'all' | 'verified' | 'unverified'
export type CompanySortBy = 'name' | 'declaration_count' | 'updated_at'
export type SortOrder = 'asc' | 'desc'

export interface CompanyListParams {
  type: CompanyType
  search?: string
  filter?: CompanyFilterType
  page?: number
  limit?: number
  sort_by?: CompanySortBy
  sort_order?: SortOrder
}
