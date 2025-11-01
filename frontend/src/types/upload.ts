import { z } from 'zod'

/**
 * File types for customs declaration documents
 * Updated in Story 3.3.1: Removed GOODLIST and TARIFF (now system-wide knowledge bases)
 */
export type FileType = 'AN' | 'BOL' | 'CO' | 'INVOICE'

/**
 * Human-readable labels for each file type
 */
export const FILE_TYPE_LABELS: Record<FileType, string> = {
  AN: 'Arrival Notice',
  BOL: 'Bill of Lading',
  CO: 'Certificate of Origin',
  INVOICE: 'Invoice',
}

/**
 * File name patterns for each file type
 */
export const FILE_NAME_PATTERNS: Record<FileType, string> = {
  AN: 'AN.pdf',
  BOL: 'BOL.pdf',
  CO: 'CO.pdf',
  INVOICE: 'INVOICE.pdf/jpg',
}

/**
 * Accepted file formats for each file type
 */
export const ACCEPTED_FORMATS: Record<FileType, string[]> = {
  AN: ['.pdf'],
  BOL: ['.pdf'],
  CO: ['.pdf'],
  INVOICE: ['.pdf', '.jpg', '.jpeg', '.png'],
}

/**
 * Accepted MIME types for each file type
 */
export const ACCEPTED_MIME_TYPES: Record<FileType, string[]> = {
  AN: ['application/pdf'],
  BOL: ['application/pdf'],
  CO: ['application/pdf'],
  INVOICE: ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'],
}

/**
 * Maximum file sizes in bytes for each file type
 */
export const MAX_FILE_SIZES: Record<FileType, number> = {
  AN: 10 * 1024 * 1024, // 10MB
  BOL: 10 * 1024 * 1024, // 10MB
  CO: 10 * 1024 * 1024, // 10MB
  INVOICE: 10 * 1024 * 1024, // 10MB for PDF, but images validated separately
}

/**
 * Maximum size for image files (5MB)
 */
export const MAX_IMAGE_SIZE = 5 * 1024 * 1024

/**
 * C/O file count limits
 */
export const MIN_CO_FILES = 1
export const RECOMMENDED_MAX_CO_FILES = 10
export const HARD_MAX_CO_FILES = 20

/**
 * Frontend state for file uploads (before submission)
 * Updated in Story 3.3.1: CO supports multiple files, removed GOODLIST and TARIFF
 */
export interface FileUploadState {
  arrival_notice: File | null
  bill_of_lading: File | null
  certificate_of_origin: File[] // Changed from File | null to File[]
  invoice: File | null
}

/**
 * Backend field names mapping to FileType
 */
export const FIELD_NAME_MAP: Record<FileType, keyof FileUploadState> = {
  AN: 'arrival_notice',
  BOL: 'bill_of_lading',
  CO: 'certificate_of_origin',
  INVOICE: 'invoice',
}

/**
 * Uploaded file metadata from backend
 */
export interface UploadedFile {
  file_type: FileType
  filename: string
  size: number // bytes
  mime_type: string
  path: string // backend storage path
  uploaded_at: string
}

/**
 * Upload API response
 */
export interface UploadResponse {
  declaration_id: string
  status: 'UPLOADED'
  created_at: string
}

/**
 * Upload error detail
 */
export interface UploadErrorDetail {
  name: string
  reason: string
}

/**
 * Upload error response (RFC 7807 Problem Details)
 */
export interface UploadErrorResponse {
  type: string
  title: string
  detail: string
  invalid_params?: UploadErrorDetail[]
}

/**
 * Zod schema for validating a single file
 */
const fileSchema = z.instanceof(File).refine((file) => file.size > 0, {
  message: 'File cannot be empty',
})

/**
 * Zod schema for validating C/O files array (1-20 files)
 */
const coFilesSchema = z
  .array(fileSchema)
  .min(MIN_CO_FILES, {
    message: 'At least 1 Certificate of Origin file is required',
  })
  .max(HARD_MAX_CO_FILES, {
    message: `Maximum ${HARD_MAX_CO_FILES} Certificate of Origin files allowed`,
  })

/**
 * Zod schema for validating all 4 required file types are present
 * Updated in Story 3.3.1: Removed GOODLIST and TARIFF, CO now array
 */
export const fileUploadSchema = z.object({
  arrival_notice: fileSchema,
  bill_of_lading: fileSchema,
  certificate_of_origin: coFilesSchema,
  invoice: fileSchema,
})

/**
 * Type inference from Zod schema
 */
export type ValidatedFileUpload = z.infer<typeof fileUploadSchema>

/**
 * Validate that all 4 required file types are present
 */
export function validateAllFilesPresent(files: FileUploadState): boolean {
  return (
    files.arrival_notice !== null &&
    files.bill_of_lading !== null &&
    files.certificate_of_origin.length >= MIN_CO_FILES &&
    files.invoice !== null
  )
}

/**
 * Get the list of missing file types
 */
export function getMissingFileTypes(files: FileUploadState): FileType[] {
  const missing: FileType[] = []

  if (!files.arrival_notice) missing.push('AN')
  if (!files.bill_of_lading) missing.push('BOL')
  if (files.certificate_of_origin.length < MIN_CO_FILES) missing.push('CO')
  if (!files.invoice) missing.push('INVOICE')

  return missing
}

/**
 * Count how many file types have been uploaded (CO counts as 1 type regardless of count)
 */
export function countUploadedFileTypes(files: FileUploadState): number {
  let count = 0
  if (files.arrival_notice) count++
  if (files.bill_of_lading) count++
  if (files.certificate_of_origin.length >= MIN_CO_FILES) count++
  if (files.invoice) count++
  return count
}

/**
 * Check if C/O file count exceeds recommended limit
 */
export function shouldWarnAboutCoFileCount(coFiles: File[]): boolean {
  return coFiles.length > RECOMMENDED_MAX_CO_FILES
}

/**
 * Get total file count across all types
 */
export function getTotalFileCount(files: FileUploadState): number {
  let count = 0
  if (files.arrival_notice) count++
  if (files.bill_of_lading) count++
  count += files.certificate_of_origin.length
  if (files.invoice) count++
  return count
}
