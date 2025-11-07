/**
 * Confidence Input Component (Updated for Story 3.6 Expansion)
 *
 * Input component with confidence-based visual indicators
 * - Green border: High confidence (>= 0.9)
 * - Yellow border: Medium confidence (0.7 - 0.89)
 * - Red border: Low confidence or null/missing value (< 0.7)
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
import { NullFieldPlaceholder } from './null-field-placeholder'

interface ConfidenceInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value'> {
  confidenceScore?: number
  showNullIndicator?: boolean
  value?: string | number | readonly string[] | null
}

export const ConfidenceInput = React.forwardRef<
  HTMLInputElement,
  ConfidenceInputProps
>(
  (
    { confidenceScore, showNullIndicator = true, className, value, ...props },
    ref
  ) => {
    // Check if value is null/undefined/empty
    const isNull = value === null || value === undefined || value === ''

    // Determine border color - red for null values, otherwise based on confidence
    const borderClass = isNull
      ? 'border-red-500'
      : getConfidenceBorderColor(confidenceScore)

    const { label, colorClass } = getConfidenceLabel(confidenceScore)

    // If no confidence score and not null, render regular input
    if (confidenceScore === undefined && !isNull) {
      return <Input ref={ref} className={className} value={value} {...props} />
    }

    return (
      <div className="space-y-1">
        {/* Show null indicator if field is empty and showNullIndicator is true */}
        {isNull && showNullIndicator && <NullFieldPlaceholder />}

        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Input
                ref={ref}
                className={cn(className, borderClass, 'border-2')}
                placeholder={isNull ? 'Enter manually...' : props.placeholder}
                value={value ?? ''}
                {...props}
              />
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              <div className="space-y-1">
                {isNull ? (
                  <>
                    <p className="text-sm font-medium text-red-600">
                      Missing Data
                    </p>
                    <p className="text-xs text-muted-foreground">
                      This field was not extracted - manual entry required
                    </p>
                  </>
                ) : (
                  <>
                    <p className={cn('text-sm font-medium', colorClass)}>
                      {label}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Field extracted with AI - review accuracy
                    </p>
                  </>
                )}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    )
  }
)

ConfidenceInput.displayName = 'ConfidenceInput'
