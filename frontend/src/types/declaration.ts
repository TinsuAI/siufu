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
 * Status Response from GET /api/declarations/{id}/status
 */
export interface StatusResponse {
  id: string
  status: DeclarationStatus
  processing_progress: number // 0.0 to 1.0
  processing_error: string | null
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
