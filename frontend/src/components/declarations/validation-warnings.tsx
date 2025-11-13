/**
 * Validation Warnings Panel Component
 *
 * Displays cross-document validation warnings prominently with:
 * - Three severity levels (error, warning, info)
 * - Expandable details for each warning
 * - Jump to Source functionality
 * - Dismiss and show/hide dismissed warnings
 * - Summary badge counts
 */

'use client'

import React from 'react'
import {
  AlertTriangle,
  XCircle,
  Info,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  X,
  Eye,
  EyeOff,
} from 'lucide-react'
import { useRouter } from '@/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { ValidationWarning } from '@/types/declaration'
import { cn } from '@/lib/utils'

interface ValidationWarningsPanelProps {
  warnings: ValidationWarning[]
  declarationId: string
  className?: string
  defaultOpen?: boolean
}

export function ValidationWarningsPanel({
  warnings,
  declarationId,
  className,
  defaultOpen = true,
}: ValidationWarningsPanelProps) {
  const router = useRouter()
  const [isOpen, setIsOpen] = React.useState(defaultOpen)
  const [showDismissed, setShowDismissed] = React.useState(false)
  const [expandedWarnings, setExpandedWarnings] = React.useState<Set<string>>(
    new Set()
  )
  const [dismissedWarnings, setDismissedWarnings] = React.useState<Set<string>>(
    new Set()
  )

  // Load dismissed warnings from localStorage
  React.useEffect(() => {
    const key = `dismissed-warnings-${declarationId}`
    const stored = localStorage.getItem(key)
    if (stored) {
      try {
        const dismissed = JSON.parse(stored) as string[]
        setDismissedWarnings(new Set(dismissed))
      } catch {
        // Failed to parse dismissed warnings from localStorage
      }
    }
  }, [declarationId])

  // Save dismissed warnings to localStorage
  const saveDismissedWarnings = (dismissed: Set<string>) => {
    const key = `dismissed-warnings-${declarationId}`
    localStorage.setItem(key, JSON.stringify(Array.from(dismissed)))
  }

  // Generate unique ID for each warning
  const getWarningId = (warning: ValidationWarning, index: number): string => {
    return warning.rule ? `${warning.rule}_${index}` : `warning_${index}`
  }

  // Toggle warning details expansion
  const toggleWarningExpansion = (warningId: string) => {
    setExpandedWarnings((prev) => {
      const next = new Set(prev)
      if (next.has(warningId)) {
        next.delete(warningId)
      } else {
        next.add(warningId)
      }
      return next
    })
  }

  // Dismiss warning
  const dismissWarning = (warningId: string) => {
    const updated = new Set(dismissedWarnings)
    updated.add(warningId)
    setDismissedWarnings(updated)
    saveDismissedWarnings(updated)
  }

  // Undismiss warning
  const undismissWarning = (warningId: string) => {
    const updated = new Set(dismissedWarnings)
    updated.delete(warningId)
    setDismissedWarnings(updated)
    saveDismissedWarnings(updated)
  }

  // Jump to source document
  const jumpToSource = (docType: string) => {
    router.push(`/declarations/${declarationId}/documents?doc=${docType}`)
  }

  // Filter warnings by dismiss status
  const activeWarnings = warnings.filter(
    (w, i) => !dismissedWarnings.has(getWarningId(w, i))
  )
  const dismissedWarningsList = warnings.filter((w, i) =>
    dismissedWarnings.has(getWarningId(w, i))
  )

  const displayedWarnings = showDismissed ? warnings : activeWarnings

  // Don't render if no warnings
  if (!warnings || warnings.length === 0) {
    return null
  }

  // Separate warnings by severity
  const errors = displayedWarnings.filter((w) => w.severity === 'error')
  const warningsOnly = displayedWarnings.filter((w) => w.severity === 'warning')
  const infos = displayedWarnings.filter((w) => w.severity === 'info')

  // Count active warnings by severity
  const activeErrors = activeWarnings.filter(
    (w) => w.severity === 'error'
  ).length
  const activeWarningsCount = activeWarnings.filter(
    (w) => w.severity === 'warning'
  ).length
  const activeInfos = activeWarnings.filter((w) => w.severity === 'info').length

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className={cn('border-yellow-500 bg-yellow-50', className)}>
        <CardHeader className="pb-3">
          <CollapsibleTrigger className="flex w-full items-center justify-between hover:opacity-80">
            <div className="flex items-center gap-2 flex-wrap">
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
              <CardTitle className="text-lg">Validation Issues</CardTitle>
              <div className="flex gap-1.5">
                {activeErrors > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    {activeErrors} error{activeErrors !== 1 ? 's' : ''}
                  </Badge>
                )}
                {activeWarningsCount > 0 && (
                  <Badge
                    variant="outline"
                    className="text-xs bg-yellow-100 text-yellow-900 border-yellow-300"
                  >
                    {activeWarningsCount} warning
                    {activeWarningsCount !== 1 ? 's' : ''}
                  </Badge>
                )}
                {activeInfos > 0 && (
                  <Badge
                    variant="outline"
                    className="text-xs bg-blue-100 text-blue-900 border-blue-300"
                  >
                    {activeInfos} info
                  </Badge>
                )}
              </div>
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
            {/* Show/Hide Dismissed Toggle */}
            {dismissedWarningsList.length > 0 && (
              <div className="flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDismissed(!showDismissed)}
                  className="text-xs"
                >
                  {showDismissed ? (
                    <>
                      <EyeOff className="h-3 w-3 mr-1" />
                      Hide dismissed ({dismissedWarningsList.length})
                    </>
                  ) : (
                    <>
                      <Eye className="h-3 w-3 mr-1" />
                      Show dismissed ({dismissedWarningsList.length})
                    </>
                  )}
                </Button>
              </div>
            )}

            {/* Errors Section */}
            {errors.length > 0 && (
              <div className="space-y-2">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-red-700">
                  <XCircle className="h-4 w-4" />
                  Errors ({errors.length}) - Must be fixed before approval
                </h4>
                <ul className="space-y-2">
                  {errors.map((error) => {
                    const warningId = getWarningId(
                      error,
                      warnings.indexOf(error)
                    )
                    const isExpanded = expandedWarnings.has(warningId)
                    const isDismissed = dismissedWarnings.has(warningId)

                    return (
                      <li
                        key={warningId}
                        className={cn(
                          'rounded-md bg-red-50 p-3 text-sm text-red-800 border border-red-200',
                          isDismissed && 'opacity-50'
                        )}
                      >
                        <div className="flex items-start gap-2">
                          <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <p className="font-medium flex-1">
                                {error.message}
                              </p>
                              <div className="flex gap-1">
                                {error.details && (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      toggleWarningExpansion(warningId)
                                    }
                                    className="h-6 px-2 text-xs"
                                  >
                                    {isExpanded ? (
                                      <ChevronUp className="h-3 w-3" />
                                    ) : (
                                      <ChevronDown className="h-3 w-3" />
                                    )}
                                  </Button>
                                )}
                                {isDismissed ? (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => undismissWarning(warningId)}
                                    className="h-6 px-2 text-xs"
                                    title="Restore warning"
                                  >
                                    <Eye className="h-3 w-3" />
                                  </Button>
                                ) : (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => dismissWarning(warningId)}
                                    className="h-6 px-2 text-xs"
                                    title="Dismiss warning"
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                )}
                              </div>
                            </div>
                            {error.field && (
                              <p className="text-xs text-red-600">
                                Field: {error.field}
                              </p>
                            )}
                            {isExpanded && error.details && (
                              <div className="mt-2 p-2 bg-red-100 rounded text-xs space-y-1">
                                {error.details.expected_value !== undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Expected:
                                    </span>{' '}
                                    {JSON.stringify(
                                      error.details.expected_value
                                    )}
                                  </p>
                                )}
                                {error.details.actual_value !== undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Actual:
                                    </span>{' '}
                                    {JSON.stringify(error.details.actual_value)}
                                  </p>
                                )}
                                {error.details.confidence !== undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Confidence:
                                    </span>{' '}
                                    {(error.details.confidence * 100).toFixed(
                                      0
                                    )}
                                    %
                                  </p>
                                )}
                                {error.details.source_docs &&
                                  error.details.source_docs.length > 0 && (
                                    <div className="flex gap-1 flex-wrap mt-2">
                                      {error.details.source_docs.map((doc) => (
                                        <Button
                                          key={doc}
                                          type="button"
                                          variant="outline"
                                          size="sm"
                                          onClick={() => jumpToSource(doc)}
                                          className="h-6 px-2 text-xs bg-white"
                                        >
                                          <ExternalLink className="h-3 w-3 mr-1" />
                                          View in {doc}
                                        </Button>
                                      ))}
                                    </div>
                                  )}
                              </div>
                            )}
                          </div>
                        </div>
                      </li>
                    )
                  })}
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
                  {warningsOnly.map((warning) => {
                    const warningId = getWarningId(
                      warning,
                      warnings.indexOf(warning)
                    )
                    const isExpanded = expandedWarnings.has(warningId)
                    const isDismissed = dismissedWarnings.has(warningId)

                    return (
                      <li
                        key={warningId}
                        className={cn(
                          'rounded-md bg-yellow-100 p-3 text-sm text-yellow-900 border border-yellow-300',
                          isDismissed && 'opacity-50'
                        )}
                      >
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <p className="font-medium flex-1">
                                {warning.message}
                              </p>
                              <div className="flex gap-1">
                                {warning.details && (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      toggleWarningExpansion(warningId)
                                    }
                                    className="h-6 px-2 text-xs"
                                  >
                                    {isExpanded ? (
                                      <ChevronUp className="h-3 w-3" />
                                    ) : (
                                      <ChevronDown className="h-3 w-3" />
                                    )}
                                  </Button>
                                )}
                                {isDismissed ? (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => undismissWarning(warningId)}
                                    className="h-6 px-2 text-xs"
                                    title="Restore warning"
                                  >
                                    <Eye className="h-3 w-3" />
                                  </Button>
                                ) : (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => dismissWarning(warningId)}
                                    className="h-6 px-2 text-xs"
                                    title="Dismiss warning"
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                )}
                              </div>
                            </div>
                            {warning.field && (
                              <p className="text-xs text-yellow-700">
                                Field: {warning.field}
                              </p>
                            )}
                            {isExpanded && warning.details && (
                              <div className="mt-2 p-2 bg-yellow-200 rounded text-xs space-y-1">
                                {warning.details.expected_value !==
                                  undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Expected:
                                    </span>{' '}
                                    {JSON.stringify(
                                      warning.details.expected_value
                                    )}
                                  </p>
                                )}
                                {warning.details.actual_value !== undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Actual:
                                    </span>{' '}
                                    {JSON.stringify(
                                      warning.details.actual_value
                                    )}
                                  </p>
                                )}
                                {warning.details.confidence !== undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Confidence:
                                    </span>{' '}
                                    {(warning.details.confidence * 100).toFixed(
                                      0
                                    )}
                                    %
                                  </p>
                                )}
                                {warning.details.source_docs &&
                                  warning.details.source_docs.length > 0 && (
                                    <div className="flex gap-1 flex-wrap mt-2">
                                      {warning.details.source_docs.map(
                                        (doc) => (
                                          <Button
                                            key={doc}
                                            type="button"
                                            variant="outline"
                                            size="sm"
                                            onClick={() => jumpToSource(doc)}
                                            className="h-6 px-2 text-xs bg-white"
                                          >
                                            <ExternalLink className="h-3 w-3 mr-1" />
                                            View in {doc}
                                          </Button>
                                        )
                                      )}
                                    </div>
                                  )}
                              </div>
                            )}
                          </div>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}

            {/* Info Section */}
            {infos.length > 0 && (
              <div className="space-y-2">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-blue-700">
                  <Info className="h-4 w-4" />
                  Information ({infos.length}) - For your awareness
                </h4>
                <ul className="space-y-2">
                  {infos.map((info) => {
                    const warningId = getWarningId(info, warnings.indexOf(info))
                    const isExpanded = expandedWarnings.has(warningId)
                    const isDismissed = dismissedWarnings.has(warningId)

                    return (
                      <li
                        key={warningId}
                        className={cn(
                          'rounded-md bg-blue-100 p-3 text-sm text-blue-900 border border-blue-300',
                          isDismissed && 'opacity-50'
                        )}
                      >
                        <div className="flex items-start gap-2">
                          <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <p className="font-medium flex-1">
                                {info.message}
                              </p>
                              <div className="flex gap-1">
                                {info.details && (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      toggleWarningExpansion(warningId)
                                    }
                                    className="h-6 px-2 text-xs"
                                  >
                                    {isExpanded ? (
                                      <ChevronUp className="h-3 w-3" />
                                    ) : (
                                      <ChevronDown className="h-3 w-3" />
                                    )}
                                  </Button>
                                )}
                                {isDismissed ? (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => undismissWarning(warningId)}
                                    className="h-6 px-2 text-xs"
                                    title="Restore warning"
                                  >
                                    <Eye className="h-3 w-3" />
                                  </Button>
                                ) : (
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => dismissWarning(warningId)}
                                    className="h-6 px-2 text-xs"
                                    title="Dismiss warning"
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                )}
                              </div>
                            </div>
                            {info.field && (
                              <p className="text-xs text-blue-700">
                                Field: {info.field}
                              </p>
                            )}
                            {isExpanded && info.details && (
                              <div className="mt-2 p-2 bg-blue-200 rounded text-xs space-y-1">
                                {info.details.expected_value !== undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Expected:
                                    </span>{' '}
                                    {JSON.stringify(
                                      info.details.expected_value
                                    )}
                                  </p>
                                )}
                                {info.details.actual_value !== undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Actual:
                                    </span>{' '}
                                    {JSON.stringify(info.details.actual_value)}
                                  </p>
                                )}
                                {info.details.confidence !== undefined && (
                                  <p>
                                    <span className="font-semibold">
                                      Confidence:
                                    </span>{' '}
                                    {(info.details.confidence * 100).toFixed(0)}
                                    %
                                  </p>
                                )}
                                {info.details.source_docs &&
                                  info.details.source_docs.length > 0 && (
                                    <div className="flex gap-1 flex-wrap mt-2">
                                      {info.details.source_docs.map((doc) => (
                                        <Button
                                          key={doc}
                                          type="button"
                                          variant="outline"
                                          size="sm"
                                          onClick={() => jumpToSource(doc)}
                                          className="h-6 px-2 text-xs bg-white"
                                        >
                                          <ExternalLink className="h-3 w-3 mr-1" />
                                          View in {doc}
                                        </Button>
                                      ))}
                                    </div>
                                  )}
                              </div>
                            )}
                          </div>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}
