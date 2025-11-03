/**
 * Save Indicator Component
 *
 * Displays the current save status (Saving, Saved, Error)
 */

'use client'

import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SaveIndicatorProps {
  isSaving: boolean
  isSuccess: boolean
  isError: boolean
  className?: string
}

export function SaveIndicator({
  isSaving,
  isSuccess,
  isError,
  className,
}: SaveIndicatorProps) {
  if (isSaving) {
    return (
      <div className={cn('flex items-center gap-2 text-sm', className)}>
        <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
        <span className="text-blue-600">Saving...</span>
      </div>
    )
  }

  if (isError) {
    return (
      <div className={cn('flex items-center gap-2 text-sm', className)}>
        <AlertCircle className="h-4 w-4 text-red-600" />
        <span className="text-red-600">Error - Changes not saved</span>
      </div>
    )
  }

  if (isSuccess) {
    return (
      <div className={cn('flex items-center gap-2 text-sm', className)}>
        <CheckCircle2 className="h-4 w-4 text-green-600" />
        <span className="text-green-600">Saved</span>
      </div>
    )
  }

  return null
}
