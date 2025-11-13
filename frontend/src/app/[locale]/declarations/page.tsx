'use client'

/**
 * Declarations History List Page
 * Story 3.9: Displays paginated, filterable, sortable list of all user's declarations
 * Story 4.3: Added i18n support and Vietnamese formatting
 */

import { useState } from 'react'
import { useRouter } from '@/navigation'
import {
  Eye,
  Download,
  Trash2,
  ArrowUpDown,
  Search,
  Loader2,
  X,
  Plus,
} from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useDebounce } from 'use-debounce'
import { useDeclarations } from '@/hooks/use-declarations'
import { DeclarationStatusBadge } from '@/components/declarations/declaration-status-badge'
import { exportDeclaration } from '@/lib/api'
import { DeclarationStatus } from '@/types/declaration'
import { useFormatting } from '@/lib/format-utils'
import { useStatusLabels } from '@/lib/status-utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/hooks/use-toast'
import Link from 'next/link'

export default function DeclarationsListPage() {
  const router = useRouter()
  const { toast } = useToast()
  const t = useTranslations('common.declarations')
  const tActions = useTranslations('common.actions')
  const tCommon = useTranslations('common.common')
  const { formatDateTime } = useFormatting()
  const { getStatusLabel } = useStatusLabels()

  // Pagination and filter state
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(
    undefined
  )
  const [searchInput, setSearchInput] = useState('')
  const [sortBy, setSortBy] = useState<'created_at' | 'status'>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Debounce search input by 500ms
  const [debouncedSearch] = useDebounce(searchInput, 500)

  // Fetch declarations with current filters
  const { data, isLoading, error, deleteMutation } = useDeclarations({
    page,
    limit: 20,
    status: statusFilter,
    search: debouncedSearch || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  })

  // Delete confirmation dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [declarationToDelete, setDeclarationToDelete] = useState<string | null>(
    null
  )

  // Download loading state (track which declaration is being downloaded)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  // Toggle sort order for a column
  const toggleSort = (column: 'created_at' | 'status') => {
    if (sortBy === column) {
      // Toggle order if same column
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      // Set new column with desc as default
      setSortBy(column)
      setSortOrder('desc')
    }
    // Reset to page 1 when sorting changes
    setPage(1)
  }

  // Handle delete confirmation
  const handleDeleteClick = (id: string) => {
    setDeclarationToDelete(id)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!declarationToDelete) return

    try {
      await deleteMutation.mutateAsync(declarationToDelete)
      toast({
        title: tCommon('success'),
        description: t('messages.deleteSuccess'),
      })
      setDeleteDialogOpen(false)
      setDeclarationToDelete(null)
    } catch (error) {
      toast({
        title: tCommon('error'),
        description:
          error instanceof Error ? error.message : t('messages.deleteError'),
        variant: 'error',
      })
    }
  }

  // Handle download
  const handleDownload = async (id: string) => {
    setDownloadingId(id)
    try {
      const blob = await exportDeclaration(id)
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `declaration_${id}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        title: tCommon('success'),
        description: t('messages.exportSuccess'),
      })
    } catch (error) {
      toast({
        title: tCommon('error'),
        description:
          error instanceof Error ? error.message : t('messages.exportError'),
        variant: 'error',
      })
    } finally {
      setDownloadingId(null)
    }
  }

  // Clear search
  const handleClearSearch = () => {
    setSearchInput('')
    setPage(1)
  }

  // Handle status filter change
  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value === 'all' ? undefined : value)
    setPage(1) // Reset to page 1 when filter changes
  }

  // Loading state
  if (isLoading && !data) {
    return (
      <div className="container mx-auto px-6 py-8">
        {/* Header with Title and Create Button */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-slate-700">{t('title')}</h1>
          <Link href="/upload">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              {t('createNew')}
            </Button>
          </Link>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-3 text-slate-600">{t('messages.loading')}</span>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-6 py-8">
        {/* Header with Title and Create Button */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-slate-700">{t('title')}</h1>
          <Link href="/upload">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              {t('createNew')}
            </Button>
          </Link>
        </div>
        <div className="rounded-lg bg-red-50 border border-red-200 p-4">
          <p className="text-red-800">
            {t('messages.error', { message: error.message })}
          </p>
        </div>
      </div>
    )
  }

  // Empty state
  if (!data || data.items.length === 0) {
    return (
      <div className="container mx-auto px-6 py-8">
        {/* Header with Title and Create Button */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-slate-700">
            Declaration History
          </h1>
          <Link href="/upload">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create New Declaration
            </Button>
          </Link>
        </div>

        {/* Search and Filters */}
        <div className="flex gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by Declaration ID..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="pl-10 pr-10"
            />
            {searchInput && (
              <button
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <Select
            value={statusFilter || 'all'}
            onValueChange={handleStatusFilterChange}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value={DeclarationStatus.UPLOADED}>
                Uploaded
              </SelectItem>
              <SelectItem value={DeclarationStatus.PROCESSING}>
                Processing
              </SelectItem>
              <SelectItem value={DeclarationStatus.READY_FOR_REVIEW}>
                Ready for Review
              </SelectItem>
              <SelectItem value={DeclarationStatus.APPROVED}>
                Approved
              </SelectItem>
              <SelectItem value={DeclarationStatus.REJECTED}>
                Rejected
              </SelectItem>
              <SelectItem value={DeclarationStatus.FAILED}>Failed</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="rounded-lg bg-slate-50 border border-slate-200 p-12 text-center">
          <p className="text-slate-600 text-lg mb-4">
            {t('messages.noDeclarations')}
          </p>
          <Link href="/upload">
            <Button>{t('messages.uploadDeclaration')}</Button>
          </Link>
        </div>
      </div>
    )
  }

  const { items, total, total_pages } = data

  return (
    <div className="container mx-auto px-6 py-8">
      {/* Header with Title and Create Button */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-slate-700">
          Declaration History
        </h1>
        <Link href="/upload">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create New Declaration
          </Button>
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder={t('filters.search')}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-10 pr-10"
          />
          {searchInput && (
            <button
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <Select
          value={statusFilter || 'all'}
          onValueChange={handleStatusFilterChange}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder={t('filters.allStatuses')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('filters.allStatuses')}</SelectItem>
            <SelectItem value={DeclarationStatus.UPLOADED}>
              {getStatusLabel(DeclarationStatus.UPLOADED)}
            </SelectItem>
            <SelectItem value={DeclarationStatus.PROCESSING}>
              {getStatusLabel(DeclarationStatus.PROCESSING)}
            </SelectItem>
            <SelectItem value={DeclarationStatus.READY_FOR_REVIEW}>
              {getStatusLabel(DeclarationStatus.READY_FOR_REVIEW)}
            </SelectItem>
            <SelectItem value={DeclarationStatus.APPROVED}>
              {getStatusLabel(DeclarationStatus.APPROVED)}
            </SelectItem>
            <SelectItem value={DeclarationStatus.REJECTED}>
              {getStatusLabel(DeclarationStatus.REJECTED)}
            </SelectItem>
            <SelectItem value={DeclarationStatus.FAILED}>
              {getStatusLabel(DeclarationStatus.FAILED)}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm mb-6">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">
                {t('table.declarationId')}
              </TableHead>
              <TableHead>
                <button
                  onClick={() => toggleSort('created_at')}
                  className="flex items-center gap-2 hover:text-slate-900 font-medium"
                >
                  {t('table.uploadDate')}
                  <ArrowUpDown className="h-4 w-4" />
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => toggleSort('status')}
                  className="flex items-center gap-2 hover:text-slate-900 font-medium"
                >
                  {t('table.status')}
                  <ArrowUpDown className="h-4 w-4" />
                </button>
              </TableHead>
              <TableHead className="text-right">
                {t('table.productsCount')}
              </TableHead>
              <TableHead className="text-right">{t('table.actions')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((declaration) => {
              const canReview = [
                DeclarationStatus.READY_FOR_REVIEW,
                DeclarationStatus.APPROVED,
                DeclarationStatus.REJECTED,
              ].includes(declaration.status as DeclarationStatus)

              const canDownload =
                declaration.status === DeclarationStatus.APPROVED

              return (
                <TableRow key={declaration.id}>
                  <TableCell className="font-mono text-sm">
                    <Link
                      href={`/declarations/${declaration.id}`}
                      className="text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      {declaration.id}
                    </Link>
                  </TableCell>
                  <TableCell>
                    {formatDateTime(declaration.created_at)}
                  </TableCell>
                  <TableCell>
                    <DeclarationStatusBadge
                      status={declaration.status as DeclarationStatus}
                    />
                  </TableCell>
                  <TableCell className="text-right">
                    {declaration.products_count}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {canReview && (
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() =>
                            router.push(
                              `/declarations/${declaration.id}/review`
                            )
                          }
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          {t('actions.review')}
                        </Button>
                      )}

                      {canDownload && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownload(declaration.id)}
                          disabled={downloadingId === declaration.id}
                          className="text-green-600 border-green-600 hover:bg-green-50"
                        >
                          {downloadingId === declaration.id ? (
                            <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                          ) : (
                            <Download className="h-4 w-4 mr-1" />
                          )}
                          {t('actions.download')}
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteClick(declaration.id)}
                        className="text-red-600 border-red-600 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        {t('actions.delete')}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600">
          {t('pagination.showing', {
            start: (page - 1) * 20 + 1,
            end: Math.min(page * 20, total),
            total,
          })}
        </p>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
          >
            {tActions('previous')}
          </Button>

          {/* Page numbers */}
          <div className="flex items-center gap-1">
            {/* Always show first page */}
            {page > 3 && (
              <>
                <Button
                  variant={page === 1 ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPage(1)}
                >
                  1
                </Button>
                {page > 4 && <span className="px-2 text-slate-400">...</span>}
              </>
            )}

            {/* Show 5 pages centered around current page */}
            {Array.from({ length: total_pages }, (_, i) => i + 1)
              .filter((pageNum) => {
                // Show current page and 2 pages on each side
                return pageNum >= page - 2 && pageNum <= page + 2
              })
              .map((pageNum) => (
                <Button
                  key={pageNum}
                  variant={page === pageNum ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum}
                </Button>
              ))}

            {/* Always show last page */}
            {page < total_pages - 2 && (
              <>
                {page < total_pages - 3 && (
                  <span className="px-2 text-slate-400">...</span>
                )}
                <Button
                  variant={page === total_pages ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPage(total_pages)}
                >
                  {total_pages}
                </Button>
              </>
            )}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page + 1)}
            disabled={page === total_pages}
          >
            {tActions('next')}
          </Button>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('dialog.deleteTitle')}</DialogTitle>
            <DialogDescription>
              {t('dialog.deleteDescription')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deleteMutation.isPending}
            >
              {tActions('cancel')}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t('messages.deleting')}
                </>
              ) : (
                t('actions.delete')
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
