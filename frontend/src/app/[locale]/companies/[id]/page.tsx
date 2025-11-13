/**
 * Company Details/Edit Page (Story 3.10)
 * View and edit company information
 */

'use client'

import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useRouter } from '@/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Building2,
  Edit,
  Save,
  X,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  FileText,
} from 'lucide-react'
import {
  useCompany,
  useUpdateCompany,
  useDeleteCompany,
} from '@/hooks/use-companies'
import type {
  CompanyType,
  ImporterDetail,
  ExporterDetail,
} from '@/types/company'
import { toast } from 'sonner'

// Validation schemas
const importerSchema = z.object({
  tax_code: z.string().min(1, 'Tax code is required').max(20),
  name: z.string().min(1, 'Name is required').max(255),
  postal_code: z.string().max(20).optional().nullable(),
  address: z.string().max(500).optional().nullable(),
  phone: z.string().max(50).optional().nullable(),
})

const exporterSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  country_code: z.string().length(2, 'Country code must be 2 characters'),
  address_line1: z.string().max(255).optional().nullable(),
  address_line2: z.string().max(255).optional().nullable(),
  address_line3: z.string().max(255).optional().nullable(),
})

type ImporterFormData = z.infer<typeof importerSchema>
type ExporterFormData = z.infer<typeof exporterSchema>

interface CompanyDetailsPageProps {
  params: Promise<{ id: string }>
}

export default function CompanyDetailsPage({
  params,
}: CompanyDetailsPageProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const type = (searchParams.get('type') || 'importers') as CompanyType
  const startInEditMode = searchParams.get('mode') === 'edit'
  const [isEditing, setIsEditing] = useState(startInEditMode)

  // Unwrap params promise (Next.js 15)
  const { id } = React.use(params)

  // Fetch company data
  const { data: company, isLoading, error } = useCompany(id, type)

  // Mutations
  const updateMutation = useUpdateCompany()
  const deleteMutation = useDeleteCompany()

  // Determine which schema to use
  const isImporter = type === 'importers'
  const schema = isImporter ? importerSchema : exporterSchema

  // Form setup
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: isImporter
      ? {
          tax_code: '',
          name: '',
          postal_code: '',
          address: '',
          phone: '',
        }
      : {
          name: '',
          country_code: '',
          address_line1: '',
          address_line2: '',
          address_line3: '',
        },
  })

  // Update form when company data loads
  useEffect(() => {
    if (company) {
      if (isImporter) {
        const importerData = company as ImporterDetail
        form.reset({
          tax_code: importerData.tax_code,
          name: importerData.name,
          postal_code: importerData.postal_code || '',
          address: importerData.address || '',
          phone: importerData.phone || '',
        })
      } else {
        const exporterData = company as ExporterDetail
        form.reset({
          name: exporterData.name,
          country_code: exporterData.country_code,
          address_line1: exporterData.address_line1 || '',
          address_line2: exporterData.address_line2 || '',
          address_line3: exporterData.address_line3 || '',
        })
      }
    }
  }, [company, form, isImporter])

  // Handlers
  const handleSave = async (data: ImporterFormData | ExporterFormData) => {
    try {
      await updateMutation.mutateAsync({
        id,
        type,
        data,
      })
      toast.success('Company updated successfully')
      setIsEditing(false)
    } catch (error) {
      toast.error(`Failed to update company: ${(error as Error).message}`)
    }
  }

  const handleDelete = async () => {
    const companyName = company?.name || 'this company'
    const declarationCount = company?.declaration_count || 0

    if (
      confirm(
        `Are you sure you want to delete ${companyName}? This will unlink ${declarationCount} declaration(s).`
      )
    ) {
      try {
        await deleteMutation.mutateAsync({ id, type })
        toast.success('Company deleted successfully')
        router.push('/companies')
      } catch (error) {
        toast.error(`Failed to delete company: ${(error as Error).message}`)
      }
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-center py-12">Loading company details...</div>
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-center py-12 text-red-600">
          Error loading company: {error?.message || 'Company not found'}
        </div>
      </div>
    )
  }

  const isImporterCompany = isImporter && 'tax_code' in company

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/companies')}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Companies
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Building2 className="h-8 w-8" />
              {company.name}
            </h1>
            <p className="text-muted-foreground mt-1">
              {isImporterCompany
                ? `Tax Code: ${(company as ImporterDetail).tax_code}`
                : `Country: ${(company as ExporterDetail).country_code}`}
            </p>
          </div>
          <div className="flex items-center gap-2">
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
      </div>

      {/* Company Details */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Company Information</CardTitle>
              <CardDescription>
                {isEditing ? 'Edit company details' : 'View company details'}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {!isEditing ? (
                <>
                  <Button onClick={() => setIsEditing(true)} size="sm">
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleDelete}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    onClick={form.handleSubmit(handleSave)}
                    size="sm"
                    disabled={updateMutation.isPending}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsEditing(false)
                      form.reset()
                    }}
                    disabled={updateMutation.isPending}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-4">
            {isImporterCompany ? (
              <>
                <div>
                  <Label htmlFor="tax_code">Tax Code *</Label>
                  <Input
                    id="tax_code"
                    {...form.register('tax_code')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                  {form.formState.errors.tax_code && (
                    <p className="text-sm text-red-600 mt-1">
                      {form.formState.errors.tax_code.message}
                    </p>
                  )}
                </div>
                <div>
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    {...form.register('name')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                  {form.formState.errors.name && (
                    <p className="text-sm text-red-600 mt-1">
                      {form.formState.errors.name.message}
                    </p>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="postal_code">Postal Code</Label>
                    <Input
                      id="postal_code"
                      {...form.register('postal_code')}
                      disabled={!isEditing}
                      className={!isEditing ? 'bg-muted' : ''}
                    />
                  </div>
                  <div>
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      {...form.register('phone')}
                      disabled={!isEditing}
                      className={!isEditing ? 'bg-muted' : ''}
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="address">Address</Label>
                  <Input
                    id="address"
                    {...form.register('address')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    {...form.register('name')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                  {form.formState.errors.name && (
                    <p className="text-sm text-red-600 mt-1">
                      {form.formState.errors.name.message}
                    </p>
                  )}
                </div>
                <div>
                  <Label htmlFor="country_code">Country Code *</Label>
                  <Input
                    id="country_code"
                    {...form.register('country_code')}
                    disabled={!isEditing}
                    maxLength={2}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                  {form.formState.errors.country_code && (
                    <p className="text-sm text-red-600 mt-1">
                      {form.formState.errors.country_code.message}
                    </p>
                  )}
                </div>
                <div>
                  <Label htmlFor="address_line1">Address Line 1</Label>
                  <Input
                    id="address_line1"
                    {...form.register('address_line1')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                </div>
                <div>
                  <Label htmlFor="address_line2">Address Line 2</Label>
                  <Input
                    id="address_line2"
                    {...form.register('address_line2')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                </div>
                <div>
                  <Label htmlFor="address_line3">Address Line 3</Label>
                  <Input
                    id="address_line3"
                    {...form.register('address_line3')}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-muted' : ''}
                  />
                </div>
              </>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Declarations</p>
              <p className="font-medium flex items-center gap-1">
                <FileText className="h-4 w-4" />
                {company.declaration_count}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Confidence Score</p>
              <p className="font-medium">
                {(company.confidence_score * 100).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Created</p>
              <p className="font-medium">
                {new Date(company.created_at).toLocaleDateString()}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Last Updated</p>
              <p className="font-medium">
                {new Date(company.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
