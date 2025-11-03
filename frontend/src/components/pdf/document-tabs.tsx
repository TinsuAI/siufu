'use client'

import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { getDeclarationMetadata } from '@/lib/api'
import { useUIStore } from '@/stores/ui-store'

interface DocumentTabsProps {
  declarationId: string
  onDocumentChange?: (filename: string) => void
}

/**
 * Document Tabs Component
 * Displays tabs or dropdown for switching between PDF documents
 * Supports multiple C/O files per Story 3.3.1
 */
export function DocumentTabs({
  declarationId,
  onDocumentChange,
}: DocumentTabsProps) {
  const { activeDocumentTab, setActiveDocumentTab } = useUIStore()

  // Fetch declaration metadata to determine available files
  const { data: metadata, isLoading } = useQuery({
    queryKey: ['declarations', declarationId, 'metadata'],
    queryFn: () => getDeclarationMetadata(declarationId),
    enabled: !!declarationId,
  })

  if (isLoading) {
    return (
      <div className="flex gap-2">
        <div className="h-10 w-32 animate-pulse rounded bg-muted" />
        <div className="h-10 w-32 animate-pulse rounded bg-muted" />
        <div className="h-10 w-32 animate-pulse rounded bg-muted" />
      </div>
    )
  }

  if (!metadata) {
    return null
  }

  // Build list of available documents
  const documents: Array<{ label: string; filename: string; type: string }> = []

  if (metadata.uploaded_files.arrival_notice) {
    documents.push({
      label: 'Arrival Notice',
      filename: metadata.uploaded_files.arrival_notice,
      type: 'AN',
    })
  }

  if (metadata.uploaded_files.bill_of_lading) {
    documents.push({
      label: 'Bill of Lading',
      filename: metadata.uploaded_files.bill_of_lading,
      type: 'BOL',
    })
  }

  // Handle multiple C/O files
  if (metadata.uploaded_files.certificate_of_origin) {
    const coFiles = metadata.uploaded_files.certificate_of_origin
    if (Array.isArray(coFiles)) {
      // New format: Multiple C/O files (CO_1.pdf, CO_2.pdf, ...)
      coFiles.forEach((filename, index) => {
        documents.push({
          label: `C/O #${index + 1}`,
          filename,
          type: `CO_${index + 1}`,
        })
      })
    } else {
      // Old format: Single C/O file (CO.pdf) - backwards compatibility
      documents.push({
        label: 'Certificate of Origin',
        filename: coFiles,
        type: 'CO',
      })
    }
  }

  if (metadata.uploaded_files.invoice) {
    documents.push({
      label: 'Invoice',
      filename: metadata.uploaded_files.invoice,
      type: 'INVOICE',
    })
  }

  const handleDocumentSelect = (filename: string) => {
    const doc = documents.find((d) => d.filename === filename)
    if (doc) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setActiveDocumentTab(doc.type as any) // Update Zustand store
      onDocumentChange?.(filename)
    }
  }

  // Get current document
  const currentDocument = documents.find((d) => d.type === activeDocumentTab)
  const currentFilename = currentDocument?.filename || documents[0]?.filename

  // Count C/O files
  const coCount = documents.filter((d) => d.type.startsWith('CO')).length

  // If 5+ C/O files, use dropdown for C/O instead of tabs
  if (coCount >= 5) {
    // Grouped layout: Tabs for AN/BOL/Invoice, Dropdown for C/O
    const nonCODocs = documents.filter((d) => !d.type.startsWith('CO'))
    const coDocs = documents.filter((d) => d.type.startsWith('CO'))

    return (
      <div className="flex flex-wrap gap-2">
        {nonCODocs.map((doc) => (
          <Button
            key={doc.type}
            variant={currentFilename === doc.filename ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleDocumentSelect(doc.filename)}
          >
            {doc.label}
          </Button>
        ))}

        {/* C/O Dropdown */}
        {coDocs.length > 0 && (
          <Select
            value={
              coDocs.find((d) => d.filename === currentFilename)?.filename || ''
            }
            onValueChange={handleDocumentSelect}
          >
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Certificate of Origin" />
            </SelectTrigger>
            <SelectContent>
              {coDocs.map((doc) => (
                <SelectItem key={doc.type} value={doc.filename}>
                  {doc.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>
    )
  }

  // Default: All tabs (< 5 C/O files)
  return (
    <div className="flex flex-wrap gap-2">
      {documents.map((doc) => (
        <Button
          key={doc.type}
          variant={currentFilename === doc.filename ? 'default' : 'outline'}
          size="sm"
          onClick={() => handleDocumentSelect(doc.filename)}
        >
          {doc.label}
        </Button>
      ))}
    </div>
  )
}
