/**
 * Field Label with Jump-to-Source Button (Story 3.7)
 *
 * Displays field label with optional "View Source" button that jumps
 * to the source location in the PDF viewer
 */

'use client'

import React from 'react'
import { Eye } from 'lucide-react'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { jumpToSource, hasSourceMetadata } from '@/lib/jump-navigation'
import type { SourceMetadataMap } from '@/lib/jump-navigation'
import { cn } from '@/lib/utils'

type FieldLabelVariant = 'full' | 'icon-only'

interface FieldLabelProps {
  htmlFor?: string
  label: React.ReactNode
  fieldPath: string
  sourceMetadata: SourceMetadataMap | null | undefined
  className?: string
  variant?: FieldLabelVariant
  hideWhenNoSource?: boolean
}

/**
 * Field label with optional "View Source" icon button
 *
 * Shows eye icon next to fields with source metadata, tooltip for calculated fields
 */
export function FieldLabel({
  htmlFor,
  label,
  fieldPath,
  sourceMetadata,
  className,
  variant = 'full',
  hideWhenNoSource = false,
}: FieldLabelProps) {
  const hasSource = hasSourceMetadata(fieldPath, sourceMetadata)

  const handleViewSource = () => {
    if (sourceMetadata) {
      jumpToSource(fieldPath, sourceMetadata)
    }
  }

  const wrapperClassName = cn(
    variant === 'icon-only'
      ? 'inline-flex items-center'
      : 'flex items-center gap-2',
    className
  )

  if (!hasSource && hideWhenNoSource && variant === 'icon-only') {
    return null
  }

  return (
    <div className={wrapperClassName}>
      {variant === 'full' && <Label htmlFor={htmlFor}>{label}</Label>}

      {hasSource && sourceMetadata ? (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className={cn(
                  'h-5 w-5 hover:bg-primary/10',
                  variant === 'icon-only' ? '' : undefined
                )}
                onClick={handleViewSource}
                aria-label={`View source for ${
                  typeof label === 'string' ? label : 'field'
                }`}
              >
                <Eye className="h-3.5 w-3.5 text-primary" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>View in source document</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      ) : !hasSource ? (
        hideWhenNoSource && variant === 'icon-only' ? null : (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 cursor-not-allowed opacity-40"
                  disabled
                  aria-label={`No source for ${
                    typeof label === 'string' ? label : 'field'
                  }`}
                >
                  <Eye className="h-3.5 w-3.5 text-muted-foreground" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Calculated field - no source</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )
      ) : null}
    </div>
  )
}
