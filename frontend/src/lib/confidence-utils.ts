/**
 * Confidence Score Utilities
 *
 * Utilities for working with confidence scores and applying visual indicators
 */

/**
 * Get Tailwind CSS classes for confidence-based border color
 * @param score - Confidence score (0.0 to 1.0)
 * @returns Tailwind class string for border color
 */
export function getConfidenceBorderColor(score: number | undefined): string {
  if (score === undefined) {
    return 'border-border' // Default border color
  }

  if (score > 0.9) {
    return 'border-green-500 focus:border-green-600'
  } else if (score >= 0.7) {
    return 'border-yellow-500 focus:border-yellow-600'
  } else {
    return 'border-red-500 focus:border-red-600'
  }
}

/**
 * Get confidence label and color for display
 * @param score - Confidence score (0.0 to 1.0)
 * @returns Object with label text and color class
 */
export function getConfidenceLabel(score: number | undefined): {
  label: string
  colorClass: string
} {
  if (score === undefined) {
    return {
      label: 'No confidence data',
      colorClass: 'text-gray-500',
    }
  }

  const percentage = Math.round(score * 100)

  if (score > 0.9) {
    return {
      label: `${percentage}% confidence (High)`,
      colorClass: 'text-green-600',
    }
  } else if (score >= 0.7) {
    return {
      label: `${percentage}% confidence (Medium)`,
      colorClass: 'text-yellow-600',
    }
  } else {
    return {
      label: `${percentage}% confidence (Low)`,
      colorClass: 'text-red-600',
    }
  }
}

/**
 * Get confidence score for a field path
 * @param confidenceScores - Map of field paths to confidence scores
 * @param fieldPath - Dot-notation field path (e.g., "company_info.importer_name")
 * @returns Confidence score or undefined if not found
 */
export function getFieldConfidence(
  confidenceScores: Record<string, number>,
  fieldPath: string
): number | undefined {
  return confidenceScores[fieldPath]
}
