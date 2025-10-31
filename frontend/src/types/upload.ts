import { z } from 'zod';

/**
 * File types for customs declaration documents
 */
export type FileType = 'AN' | 'BOL' | 'CO' | 'INVOICE' | 'GOODLIST' | 'TARIFF';

/**
 * Human-readable labels for each file type
 */
export const FILE_TYPE_LABELS: Record<FileType, string> = {
  AN: 'Arrival Notice',
  BOL: 'Bill of Lading',
  CO: 'Certificate of Origin',
  INVOICE: 'Invoice',
  GOODLIST: 'Good List',
  TARIFF: 'EXIM Tariff',
};

/**
 * File name patterns for each file type
 */
export const FILE_NAME_PATTERNS: Record<FileType, string> = {
  AN: 'AN.pdf',
  BOL: 'BOL.pdf',
  CO: 'CO.pdf',
  INVOICE: 'INVOICE.pdf/jpg',
  GOODLIST: 'goodlist.xlsx',
  TARIFF: 'tariff.xlsx',
};

/**
 * Accepted file formats for each file type
 */
export const ACCEPTED_FORMATS: Record<FileType, string[]> = {
  AN: ['.pdf'],
  BOL: ['.pdf'],
  CO: ['.pdf'],
  INVOICE: ['.pdf', '.jpg', '.jpeg', '.png'],
  GOODLIST: ['.xls', '.xlsx'],
  TARIFF: ['.xls', '.xlsx'],
};

/**
 * Accepted MIME types for each file type
 */
export const ACCEPTED_MIME_TYPES: Record<FileType, string[]> = {
  AN: ['application/pdf'],
  BOL: ['application/pdf'],
  CO: ['application/pdf'],
  INVOICE: ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'],
  GOODLIST: ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
  TARIFF: ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
};

/**
 * Maximum file sizes in bytes for each file type
 */
export const MAX_FILE_SIZES: Record<FileType, number> = {
  AN: 10 * 1024 * 1024, // 10MB
  BOL: 10 * 1024 * 1024, // 10MB
  CO: 10 * 1024 * 1024, // 10MB
  INVOICE: 10 * 1024 * 1024, // 10MB for PDF, but images validated separately
  GOODLIST: 2 * 1024 * 1024, // 2MB
  TARIFF: 2 * 1024 * 1024, // 2MB
};

/**
 * Maximum size for image files (5MB)
 */
export const MAX_IMAGE_SIZE = 5 * 1024 * 1024;

/**
 * Frontend state for file uploads (before submission)
 */
export interface FileUploadState {
  arrival_notice: File | null;
  bill_of_lading: File | null;
  certificate_of_origin: File | null;
  invoice: File | null;
  good_list: File | null;
  exim_tariff: File | null;
}

/**
 * Backend field names mapping to FileType
 */
export const FIELD_NAME_MAP: Record<FileType, keyof FileUploadState> = {
  AN: 'arrival_notice',
  BOL: 'bill_of_lading',
  CO: 'certificate_of_origin',
  INVOICE: 'invoice',
  GOODLIST: 'good_list',
  TARIFF: 'exim_tariff',
};

/**
 * Uploaded file metadata from backend
 */
export interface UploadedFile {
  file_type: FileType;
  filename: string;
  size: number; // bytes
  mime_type: string;
  path: string; // backend storage path
  uploaded_at: string;
}

/**
 * Upload API response
 */
export interface UploadResponse {
  declaration_id: string;
  status: 'UPLOADED';
  created_at: string;
}

/**
 * Upload error detail
 */
export interface UploadErrorDetail {
  name: string;
  reason: string;
}

/**
 * Upload error response (RFC 7807 Problem Details)
 */
export interface UploadErrorResponse {
  type: string;
  title: string;
  detail: string;
  invalid_params?: UploadErrorDetail[];
}

/**
 * Zod schema for validating a single file
 */
const fileSchema = z.instanceof(File).refine((file) => file.size > 0, {
  message: 'File cannot be empty',
});

/**
 * Zod schema for validating all 6 files are present
 */
export const fileUploadSchema = z.object({
  arrival_notice: fileSchema,
  bill_of_lading: fileSchema,
  certificate_of_origin: fileSchema,
  invoice: fileSchema,
  good_list: fileSchema,
  exim_tariff: fileSchema,
});

/**
 * Type inference from Zod schema
 */
export type ValidatedFileUpload = z.infer<typeof fileUploadSchema>;

/**
 * Validate that all 6 files are present
 */
export function validateAllFilesPresent(files: FileUploadState): boolean {
  return Object.values(files).every((file) => file !== null);
}

/**
 * Get the list of missing file types
 */
export function getMissingFileTypes(files: FileUploadState): FileType[] {
  const missing: FileType[] = [];

  if (!files.arrival_notice) missing.push('AN');
  if (!files.bill_of_lading) missing.push('BOL');
  if (!files.certificate_of_origin) missing.push('CO');
  if (!files.invoice) missing.push('INVOICE');
  if (!files.good_list) missing.push('GOODLIST');
  if (!files.exim_tariff) missing.push('TARIFF');

  return missing;
}

/**
 * Count how many files have been uploaded
 */
export function countUploadedFiles(files: FileUploadState): number {
  return Object.values(files).filter((file) => file !== null).length;
}
