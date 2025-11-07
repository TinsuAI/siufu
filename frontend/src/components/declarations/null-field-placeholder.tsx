/**
 * Null Field Placeholder Component (Story 3.6 Expansion)
 *
 * Shows warning indicator for null/missing fields that require manual entry
 */

'use client'

import React from 'react'
import { AlertTriangle } from 'lucide-react'

export function NullFieldPlaceholder() {
  return (
    <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-2 rounded mb-1">
      <AlertTriangle className="h-4 w-4 flex-shrink-0" />
      <span>Not extracted - manual entry required</span>
    </div>
  )
}
