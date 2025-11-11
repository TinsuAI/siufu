/**
 * Status and Stage Label Utilities
 * Story 4.3: Translatable status and processing stage labels
 */

'use client'

import { useTranslations } from 'next-intl'
import { DeclarationStatus, ProcessingStage } from '@/types/declaration'

/**
 * Hook for getting translated status and stage labels
 * @returns Functions to get localized labels for statuses and stages
 */
export function useStatusLabels() {
  const t = useTranslations('status')

  /**
   * Get translated label for a processing stage
   * @param stage ProcessingStage enum value
   * @returns Translated stage label
   */
  const getStageLabel = (stage: ProcessingStage): string => {
    return t(`stages.${stage}`)
  }

  /**
   * Get translated label for a declaration status
   * @param status DeclarationStatus enum value
   * @returns Translated status label
   */
  const getStatusLabel = (status: DeclarationStatus): string => {
    return t(`statuses.${status}`)
  }

  return {
    getStageLabel,
    getStatusLabel,
  }
}
