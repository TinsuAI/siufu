/**
 * Corrections Log Panel Component (Story 3.6 Expansion)
 *
 * Displays all field corrections flagged by the user with CSV export
 */

'use client'

import React from 'react'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  Download,
  ChevronDown,
  ChevronUp,
  Image as ImageIcon,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getCorrections, downloadCorrectionsCSV } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'

interface CorrectionsLogPanelProps {
  declarationId: string
}

/**
 * Format field path into human-readable label
 * Example: "importer.tax_code" → "Importer › Tax Code"
 */
function formatFieldName(fieldPath: string): string {
  const parts = fieldPath.split('.')
  return parts
    .map((p) => p.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()))
    .join(' › ')
}

export function CorrectionsLogPanel({
  declarationId,
}: CorrectionsLogPanelProps) {
  const [isOpen, setIsOpen] = React.useState(false)

  // Query for corrections
  const { data, isLoading, isError } = useQuery({
    queryKey: ['declarations', declarationId, 'corrections'],
    queryFn: () => getCorrections(declarationId),
    enabled: !!declarationId,
  })

  const corrections = data?.corrections || []
  const hasCorrections = corrections.length > 0

  // Don't show panel if no corrections
  if (!hasCorrections && !isLoading) {
    return null
  }

  const handleExportCSV = async () => {
    try {
      await downloadCorrectionsCSV(declarationId)
    } catch {
      // Error handling - show user-friendly message
      alert('Failed to export corrections. Please try again.')
    }
  }

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className="border rounded-lg p-4 mb-6 bg-white"
    >
      <div className="flex items-center justify-between">
        <CollapsibleTrigger className="flex items-center gap-2 hover:opacity-80">
          <h3 className="text-lg font-semibold">
            Corrections Log ({corrections.length} flagged fields)
          </h3>
          {isOpen ? (
            <ChevronUp className="h-5 w-5" />
          ) : (
            <ChevronDown className="h-5 w-5" />
          )}
        </CollapsibleTrigger>

        {hasCorrections && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCSV}
            className="ml-auto"
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        )}
      </div>

      <CollapsibleContent className="mt-4">
        {isLoading && (
          <p className="text-sm text-muted-foreground">
            Loading corrections...
          </p>
        )}

        {isError && (
          <p className="text-sm text-red-600">
            Failed to load corrections. Please try again.
          </p>
        )}

        {hasCorrections && (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field Name</TableHead>
                  <TableHead>Original → Corrected</TableHead>
                  <TableHead>Expected Value</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead>Screenshots</TableHead>
                  <TableHead>Flagged By</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {corrections.map((correction) => (
                  <TableRow key={correction.id}>
                    <TableCell className="font-mono text-sm">
                      {formatFieldName(correction.field_name)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground line-through">
                          {correction.original_value || '(null)'}
                        </span>
                        <span>→</span>
                        <span className="font-medium">
                          {correction.corrected_value}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-xs">
                      <span className="font-medium text-green-700">
                        {correction.expected_value}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm bg-orange-100 text-orange-800 px-2 py-1 rounded">
                        {correction.correction_category}
                      </span>
                    </TableCell>
                    <TableCell
                      className="max-w-xs truncate"
                      title={correction.notes}
                    >
                      {correction.notes}
                    </TableCell>
                    <TableCell>
                      {correction.screenshots &&
                      correction.screenshots.length > 0 ? (
                        <div className="flex items-center gap-1">
                          <ImageIcon className="h-4 w-4 text-blue-600" />
                          <span className="text-sm text-blue-600">
                            {correction.screenshots.length}
                          </span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell>{correction.user_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(correction.created_at), {
                        addSuffix: true,
                      })}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  )
}
