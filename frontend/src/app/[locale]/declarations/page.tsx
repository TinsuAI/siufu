'use client'

/**
 * Declarations History List Page
 * Story 3.9: Displays paginated, filterable, sortable list of all user's declarations
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { format } from 'date-fns'
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
import { useDebounce } from 'use-debounce'
import { useDeclarations } from '@/hooks/use-declarations'
import { DeclarationStatusBadge } from '@/components/declarations/declaration-status-badge'
import { exportDeclaration } from '@/lib/api'
import { DeclarationStatus } from '@/types/declaration'
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
        title: 'Success',
        description: 'Declaration deleted successfully',
      })
      setDeleteDialogOpen(false)
      setDeclarationToDelete(null)
    } catch (error) {
      toast({
        title: 'Error',
        description:
          error instanceof Error
            ? error.message
            : 'Failed to delete declaration',
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
        title: 'Success',
        description: 'Declaration exported successfully',
      })
    } catch (error) {
      toast({
        title: 'Error',
        description:
          error instanceof Error
            ? error.message
            : 'Failed to export declaration',
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
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-3 text-slate-600">Loading declarations...</span>
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
        <div className="rounded-lg bg-red-50 border border-red-200 p-4">
          <p className="text-red-800">
            Error loading declarations: {error.message}
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
            No declarations found. Upload your first declaration to get started.
          </p>
          <Link href="/upload">
            <Button>Upload Declaration</Button>
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
            <SelectItem value={DeclarationStatus.UPLOADED}>Uploaded</SelectItem>
            <SelectItem value={DeclarationStatus.PROCESSING}>
              Processing
            </SelectItem>
            <SelectItem value={DeclarationStatus.READY_FOR_REVIEW}>
              Ready for Review
            </SelectItem>
            <SelectItem value={DeclarationStatus.APPROVED}>Approved</SelectItem>
            <SelectItem value={DeclarationStatus.REJECTED}>Rejected</SelectItem>
            <SelectItem value={DeclarationStatus.FAILED}>Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm mb-6">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">Declaration ID</TableHead>
              <TableHead>
                <button
                  onClick={() => toggleSort('created_at')}
                  className="flex items-center gap-2 hover:text-slate-900 font-medium"
                >
                  Upload Date
                  <ArrowUpDown className="h-4 w-4" />
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => toggleSort('status')}
                  className="flex items-center gap-2 hover:text-slate-900 font-medium"
                >
                  Status
                  <ArrowUpDown className="h-4 w-4" />
                </button>
              </TableHead>
              <TableHead className="text-right">Products Count</TableHead>
              <TableHead className="text-right">Actions</TableHead>
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
                    {format(
                      new Date(declaration.created_at),
                      'MM/dd/yyyy HH:mm'
                    )}
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
                          Review
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
                          Download
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteClick(declaration.id)}
                        className="text-red-600 border-red-600 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Delete
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
          Showing {(page - 1) * 20 + 1}-{Math.min(page * 20, total)} of {total}{' '}
          declarations
        </p>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
          >
            Previous
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
            Next
          </Button>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Declaration</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this declaration? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
