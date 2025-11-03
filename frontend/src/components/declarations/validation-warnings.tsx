/**
 * Validation Warnings Panel Component
 *
 * Displays cross-document validation warnings prominently
 */

'use client'

import React from 'react'
import { AlertTriangle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import type { ValidationWarning } from '@/types/declaration'
import { cn } from '@/lib/utils'

interface ValidationWarningsPanelProps {
  warnings: ValidationWarning[]
  className?: string
  defaultOpen?: boolean
}

export function ValidationWarningsPanel({
  warnings,
  className,
  defaultOpen = true,
}: ValidationWarningsPanelProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen)

  // Don't render if no warnings
  if (!warnings || warnings.length === 0) {
    return null
  }

  // Separate warnings by severity
  const errors = warnings.filter((w) => w.severity === 'error')
  const warningsOnly = warnings.filter((w) => w.severity === 'warning')

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className={cn('border-yellow-500 bg-yellow-50', className)}>
        <CardHeader className="pb-3">
          <CollapsibleTrigger className="flex w-full items-center justify-between hover:opacity-80">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
              <CardTitle className="text-lg">
                Validation Issues ({warnings.length})
              </CardTitle>
            </div>
            {isOpen ? (
              <ChevronUp className="h-5 w-5" />
            ) : (
              <ChevronDown className="h-5 w-5" />
            )}
          </CollapsibleTrigger>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="space-y-4">
            {/* Errors Section */}
            {errors.length > 0 && (
              <div className="space-y-2">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-red-700">
                  <XCircle className="h-4 w-4" />
                  Errors ({errors.length}) - Must be fixed before approval
                </h4>
                <ul className="space-y-2">
                  {errors.map((error, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 rounded-md bg-red-50 p-3 text-sm text-red-800 border border-red-200"
                    >
                      <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium">{error.message}</p>
                        {error.field && (
                          <p className="text-xs text-red-600 mt-1">
                            Field: {error.field}
                          </p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Warnings Section */}
            {warningsOnly.length > 0 && (
              <div className="space-y-2">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-yellow-700">
                  <AlertTriangle className="h-4 w-4" />
                  Warnings ({warningsOnly.length}) - Review recommended
                </h4>
                <ul className="space-y-2">
                  {warningsOnly.map((warning, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 rounded-md bg-yellow-100 p-3 text-sm text-yellow-900 border border-yellow-300"
                    >
                      <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium">{warning.message}</p>
                        {warning.field && (
                          <p className="text-xs text-yellow-700 mt-1">
                            Field: {warning.field}
                          </p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}
