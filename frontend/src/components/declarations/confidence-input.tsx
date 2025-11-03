/**
 * Confidence Input Component
 *
 * Input component with confidence-based visual indicators
 */

'use client'

import React from 'react'
import { Input } from '@/components/ui/input'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  getConfidenceBorderColor,
  getConfidenceLabel,
} from '@/lib/confidence-utils'
import { cn } from '@/lib/utils'

interface ConfidenceInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  confidenceScore?: number
}

export const ConfidenceInput = React.forwardRef<
  HTMLInputElement,
  ConfidenceInputProps
>(({ confidenceScore, className, ...props }, ref) => {
  const borderClass = getConfidenceBorderColor(confidenceScore)
  const { label, colorClass } = getConfidenceLabel(confidenceScore)

  // If no confidence score, render regular input
  if (confidenceScore === undefined) {
    return <Input ref={ref} className={className} {...props} />
  }

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Input
            ref={ref}
            className={cn(className, borderClass, 'border-2')}
            {...props}
          />
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <div className="space-y-1">
            <p className={cn('text-sm font-medium', colorClass)}>{label}</p>
            <p className="text-xs text-muted-foreground">
              Field extracted with AI - review accuracy
            </p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
})

ConfidenceInput.displayName = 'ConfidenceInput'
