/**
 * Companies List Page (Story 3.10)
 * Displays importers and exporters with search, filter, and pagination
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Building2,
  Search,
  Plus,
  CheckCircle2,
  AlertTriangle,
  Edit,
  Trash2,
  Calendar,
  FileText,
  Eye,
  GitMerge,
} from 'lucide-react'
import { getCompanies, deleteCompany } from '@/lib/api'
import type {
  CompanyType,
  CompanyFilterType,
  CompanySortBy,
  ImporterListItem,
  ExporterListItem,
} from '@/types/company'
import { useDebounce } from 'use-debounce'
import { toast } from 'sonner'

export default function CompaniesPage() {
  const router = useRouter()
  const queryClient = useQueryClient()

  // State
  const [activeTab, setActiveTab] = useState<CompanyType>('importers')
  const [searchInput, setSearchInput] = useState('')
  const [filter, setFilter] = useState<CompanyFilterType>('all')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState<CompanySortBy>('updated_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Debounce search input
  const [debouncedSearch] = useDebounce(searchInput, 500)

  // Fetch companies
  const { data, isLoading, error } = useQuery({
    queryKey: [
      'companies',
      activeTab,
      debouncedSearch,
      filter,
      page,
      sortBy,
      sortOrder,
    ],
    queryFn: () =>
      getCompanies({
        type: activeTab,
        search: debouncedSearch || undefined,
        filter,
        page,
        limit: 20,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: ({ id, type }: { id: string; type: CompanyType }) =>
      deleteCompany(id, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      toast.success('Company deleted successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete company: ${error.message}`)
    },
  })

  // Handlers
  const handleDelete = (id: string) => {
    if (
      confirm(
        'Are you sure you want to delete this company? This will unlink all associated declarations.'
      )
    ) {
      deleteMutation.mutate({ id, type: activeTab })
    }
  }

  const handleTabChange = (value: string) => {
    setActiveTab(value as CompanyType)
    setPage(1) // Reset to first page when switching tabs
  }

  const handleSearch = (value: string) => {
    setSearchInput(value)
    setPage(1) // Reset to first page on search
  }

  const handleFilterChange = (value: string) => {
    setFilter(value as CompanyFilterType)
    setPage(1)
  }

  const handleSortChange = (value: string) => {
    setSortBy(value as CompanySortBy)
    setPage(1)
  }

  const handleEdit = (id: string) => {
    router.push(`/companies/${id}?type=${activeTab}&mode=edit`)
  }

  const handleMerge = (id: string) => {
    router.push(`/companies/merge?type=${activeTab}&focus=${id}`)
  }

  // Render company card
  const renderCompanyCard = (company: ImporterListItem | ExporterListItem) => {
    const isImporter = 'tax_code' in company
    const lastSeen = new Date(company.updated_at).toLocaleDateString()

    return (
      <Card key={company.id} className="hover:shadow-md transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                {company.name}
              </CardTitle>
              <CardDescription className="mt-1">
                {isImporter ? (
                  <>Tax Code: {(company as ImporterListItem).tax_code}</>
                ) : (
                  <>Country: {(company as ExporterListItem).country_code}</>
                )}
              </CardDescription>
            </div>
            <div>
              {company.is_verified ? (
                <Badge variant="default" className="bg-green-500 gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Verified
                </Badge>
              ) : (
                <Badge
                  variant="secondary"
                  className="bg-yellow-500 text-white gap-1"
                >
                  <AlertTriangle className="h-3 w-3" />
                  Unverified
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <FileText className="h-4 w-4" />
                {company.declaration_count} declarations
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                Last seen: {lastSeen}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                router.push(`/companies/${company.id}?type=${activeTab}`)
              }
            >
              <Eye className="h-4 w-4 mr-1" />
              View Details
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleEdit(company.id)}
            >
              <Edit className="h-4 w-4 mr-1" />
              Edit
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleMerge(company.id)}
            >
              <GitMerge className="h-4 w-4 mr-1" />
              Merge
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-red-600 hover:text-red-700"
              onClick={() => handleDelete(company.id)}
              disabled={deleteMutation.isPending}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Building2 className="h-8 w-8" />
            Companies
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage importer and exporter master data
          </p>
        </div>
        <Button onClick={() => router.push('/companies/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Add Company
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="mb-6">
          <TabsTrigger value="importers">Importers</TabsTrigger>
          <TabsTrigger value="exporters">Exporters</TabsTrigger>
        </TabsList>

        {/* Search and Filters */}
        <div className="flex gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={
                activeTab === 'importers'
                  ? 'Search by name or tax code...'
                  : 'Search by name...'
              }
              value={searchInput}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10"
            />
          </div>

          <Select value={filter} onValueChange={handleFilterChange}>
            <SelectTrigger className="w-[200px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Companies</SelectItem>
              <SelectItem value="verified">Verified Only</SelectItem>
              <SelectItem value="unverified">Unverified Only</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={handleSortChange}>
            <SelectTrigger className="w-[200px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="declaration_count">
                Declaration Count
              </SelectItem>
              <SelectItem value="updated_at">Last Seen</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={sortOrder}
            onValueChange={(value) => setSortOrder(value as 'asc' | 'desc')}
          >
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="asc">Ascending</SelectItem>
              <SelectItem value="desc">Descending</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <TabsContent value="importers" className="mt-0">
          {isLoading ? (
            <div className="text-center py-12">Loading companies...</div>
          ) : error ? (
            <div className="text-center py-12 text-red-600">
              Error loading companies: {error.message}
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.items.map(renderCompanyCard)}
              </div>

              {/* Pagination */}
              {data.total_pages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {page} of {data.total_pages} ({data.total} companies)
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === data.total_pages}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          ) : (
            <Card className="py-12">
              <CardContent className="text-center">
                <Building2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">
                  No companies found. Companies will appear here after
                  processing declarations.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="exporters" className="mt-0">
          {isLoading ? (
            <div className="text-center py-12">Loading companies...</div>
          ) : error ? (
            <div className="text-center py-12 text-red-600">
              Error loading companies: {error.message}
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.items.map(renderCompanyCard)}
              </div>

              {/* Pagination */}
              {data.total_pages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {page} of {data.total_pages} ({data.total} companies)
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === data.total_pages}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          ) : (
            <Card className="py-12">
              <CardContent className="text-center">
                <Building2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">
                  No companies found. Companies will appear here after
                  processing declarations.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
