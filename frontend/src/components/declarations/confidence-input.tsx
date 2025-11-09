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
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  confidenceScore?: number
  showNullIndicator?: boolean
}

export const ConfidenceInput = React.forwardRef<
  HTMLInputElement,
  ConfidenceInputProps
>(
  (
    {
      confidenceScore,
      showNullIndicator = true,
      className,
      onChange,
      defaultValue,
      value,
      ...props
    },
    ref
  ) => {
    const innerRef = React.useRef<HTMLInputElement | null>(null)

    React.useImperativeHandle(ref, () => innerRef.current as HTMLInputElement)

    const resolveCurrentValue = () => {
      if (value !== undefined && value !== null) return value
      if (innerRef.current) return innerRef.current.value
      return defaultValue ?? ''
    }

    const [isNull, setIsNull] = React.useState(() => {
      const initial = value ?? defaultValue ?? ''
      return initial === '' || initial === null || initial === undefined
    })

    React.useEffect(() => {
      setIsNull(
        resolveCurrentValue() === '' ||
          resolveCurrentValue() === undefined ||
          resolveCurrentValue() === null
      )
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [value])

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      setIsNull(event.target.value === '')
      onChange?.(event)
    }

    // Check if value is null/undefined/empty
    const currentValue = resolveCurrentValue()
    const renderIsNull =
      isNull ||
      currentValue === '' ||
      currentValue === undefined ||
      currentValue === null

    // Determine border color - red for null values, otherwise based on confidence
    const borderClass = renderIsNull
      ? 'border-red-500'
      : getConfidenceBorderColor(confidenceScore)

    const { label, colorClass } = getConfidenceLabel(confidenceScore)

    const inputClassName = cn(className, borderClass, 'border-2')

    const composedRef = (node: HTMLInputElement | null) => {
      innerRef.current = node
      if (typeof ref === 'function') {
        ref(node)
      } else if (ref) {
        ref.current = node
      }
    }

    const valueProps =
      value !== undefined
        ? { value }
        : defaultValue !== undefined
          ? { defaultValue }
          : {}

    return (
      <div className="space-y-1">
        {/* Show null indicator if field is empty and showNullIndicator is true */}
        {renderIsNull && showNullIndicator && <NullFieldPlaceholder />}

        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Input
                {...props}
                {...valueProps}
                ref={composedRef}
                className={inputClassName}
                placeholder={
                  renderIsNull ? 'Enter manually...' : props.placeholder
                }
                onChange={handleChange}
              />
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              <div className="space-y-1">
                {renderIsNull ? (
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
