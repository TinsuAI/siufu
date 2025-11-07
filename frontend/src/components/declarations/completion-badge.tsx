/**
 * Completion Badge Component (Story 3.6 Expansion)
 *
 * Shows section completion status (e.g., "✓ 5/5" or "⚠️ 3/5")
 */

'use client'

import React from 'react'
import { Badge } from '@/components/ui/badge'

interface CompletionBadgeProps {
  completed: number
  total: number
}

export function CompletionBadge({ completed, total }: CompletionBadgeProps) {
  const isComplete = completed === total
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0

  return (
    <Badge
      variant={isComplete ? 'default' : 'secondary'}
      className={isComplete ? 'bg-green-600' : 'bg-yellow-600'}
    >
      {isComplete ? '✓' : '⚠️'} {completed}/{total} ({percentage}%)
    </Badge>
  )
}
