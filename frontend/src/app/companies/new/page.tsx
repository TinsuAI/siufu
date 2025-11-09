/**
 * Add New Company Page (Story 3.10)
 * Manually create a new importer or exporter
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Building2, ArrowLeft, Save, X } from 'lucide-react'
import { useCreateCompany } from '@/hooks/use-companies'
import type { CompanyType } from '@/types/company'
import { toast } from 'sonner'

// Validation schemas
const importerSchema = z.object({
  tax_code: z
    .string()
    .min(1, 'Tax code is required')
    .max(20, 'Tax code too long'),
  name: z.string().min(1, 'Name is required').max(255, 'Name too long'),
  postal_code: z.string().max(20).optional().or(z.literal('')),
  address: z.string().max(500).optional().or(z.literal('')),
  phone: z.string().max(50).optional().or(z.literal('')),
})

const exporterSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name too long'),
  country_code: z
    .string()
    .length(2, 'Country code must be exactly 2 characters (e.g., CN, US)')
    .regex(/^[A-Z]{2}$/, 'Country code must be uppercase (e.g., CN, US)'),
  address_line1: z.string().max(255).optional().or(z.literal('')),
  address_line2: z.string().max(255).optional().or(z.literal('')),
  address_line3: z.string().max(255).optional().or(z.literal('')),
})

type ImporterFormData = z.infer<typeof importerSchema>
type ExporterFormData = z.infer<typeof exporterSchema>

export default function NewCompanyPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<CompanyType>('importers')

  // Mutation
  const createMutation = useCreateCompany()

  // Forms
  const importerForm = useForm<ImporterFormData>({
    resolver: zodResolver(importerSchema),
    defaultValues: {
      tax_code: '',
      name: '',
      postal_code: '',
      address: '',
      phone: '',
    },
  })

  const exporterForm = useForm<ExporterFormData>({
    resolver: zodResolver(exporterSchema),
    defaultValues: {
      name: '',
      country_code: '',
      address_line1: '',
      address_line2: '',
      address_line3: '',
    },
  })

  // Handler
  const handleSubmit = async (data: ImporterFormData | ExporterFormData) => {
    try {
      // Convert empty strings to null for optional fields
      const cleanedData = Object.fromEntries(
        Object.entries(data).map(([key, value]) => [
          key,
          value === '' ? null : value,
        ])
      ) as typeof data

      const result = await createMutation.mutateAsync({
        type: activeTab,
        data: cleanedData,
      })

      toast.success('Company created successfully')
      router.push(`/companies/${result.id}?type=${activeTab}`)
    } catch (error) {
      toast.error(`Failed to create company: ${(error as Error).message}`)
    }
  }

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

        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Building2 className="h-8 w-8" />
          Add New Company
        </h1>
        <p className="text-muted-foreground mt-1">
          Manually create a new importer or exporter
        </p>
      </div>

      {/* Form Card */}
      <Card>
        <CardHeader>
          <CardTitle>Company Information</CardTitle>
          <CardDescription>
            Enter the details for the new company. All fields marked with * are
            required.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs
            value={activeTab}
            onValueChange={(v) => setActiveTab(v as CompanyType)}
          >
            <TabsList className="mb-6">
              <TabsTrigger value="importers">Importer</TabsTrigger>
              <TabsTrigger value="exporters">Exporter</TabsTrigger>
            </TabsList>

            {/* Importer Form */}
            <TabsContent value="importers" className="mt-0">
              <form
                onSubmit={importerForm.handleSubmit(handleSubmit)}
                className="space-y-4"
              >
                <div>
                  <Label htmlFor="importer_tax_code">
                    Tax Code *{' '}
                    <span className="text-xs text-muted-foreground">
                      (Vietnamese MST, 10 digits)
                    </span>
                  </Label>
                  <Input
                    id="importer_tax_code"
                    placeholder="e.g., 0123456789"
                    maxLength={20}
                    {...importerForm.register('tax_code')}
                  />
                  {importerForm.formState.errors.tax_code && (
                    <p className="text-sm text-red-600 mt-1">
                      {importerForm.formState.errors.tax_code.message}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="importer_name">Name *</Label>
                  <Input
                    id="importer_name"
                    placeholder="e.g., Công ty TNHH ABC"
                    maxLength={255}
                    {...importerForm.register('name')}
                  />
                  {importerForm.formState.errors.name && (
                    <p className="text-sm text-red-600 mt-1">
                      {importerForm.formState.errors.name.message}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="importer_postal_code">Postal Code</Label>
                    <Input
                      id="importer_postal_code"
                      placeholder="e.g., 700000"
                      maxLength={20}
                      {...importerForm.register('postal_code')}
                    />
                  </div>
                  <div>
                    <Label htmlFor="importer_phone">Phone</Label>
                    <Input
                      id="importer_phone"
                      placeholder="e.g., +84 28 1234 5678"
                      maxLength={50}
                      {...importerForm.register('phone')}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="importer_address">Address</Label>
                  <Input
                    id="importer_address"
                    placeholder="e.g., 123 Nguyen Hue, District 1, HCMC"
                    maxLength={500}
                    {...importerForm.register('address')}
                  />
                </div>

                <div className="flex gap-2 pt-4">
                  <Button type="submit" disabled={createMutation.isPending}>
                    <Save className="h-4 w-4 mr-2" />
                    {createMutation.isPending
                      ? 'Creating...'
                      : 'Create Importer'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.push('/companies')}
                    disabled={createMutation.isPending}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
              </form>
            </TabsContent>

            {/* Exporter Form */}
            <TabsContent value="exporters" className="mt-0">
              <form
                onSubmit={exporterForm.handleSubmit(handleSubmit)}
                className="space-y-4"
              >
                <div>
                  <Label htmlFor="exporter_name">Name *</Label>
                  <Input
                    id="exporter_name"
                    placeholder="e.g., ABC Trading Company"
                    maxLength={255}
                    {...exporterForm.register('name')}
                  />
                  {exporterForm.formState.errors.name && (
                    <p className="text-sm text-red-600 mt-1">
                      {exporterForm.formState.errors.name.message}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="exporter_country_code">
                    Country Code *{' '}
                    <span className="text-xs text-muted-foreground">
                      (ISO 3166-1 alpha-2, e.g., CN, US)
                    </span>
                  </Label>
                  <Input
                    id="exporter_country_code"
                    placeholder="e.g., CN"
                    maxLength={2}
                    {...exporterForm.register('country_code')}
                    onChange={(e) => {
                      // Auto-uppercase
                      e.target.value = e.target.value.toUpperCase()
                      exporterForm.setValue('country_code', e.target.value)
                    }}
                  />
                  {exporterForm.formState.errors.country_code && (
                    <p className="text-sm text-red-600 mt-1">
                      {exporterForm.formState.errors.country_code.message}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="exporter_address_line1">Address Line 1</Label>
                  <Input
                    id="exporter_address_line1"
                    placeholder="Street address"
                    maxLength={255}
                    {...exporterForm.register('address_line1')}
                  />
                </div>

                <div>
                  <Label htmlFor="exporter_address_line2">Address Line 2</Label>
                  <Input
                    id="exporter_address_line2"
                    placeholder="City, Province"
                    maxLength={255}
                    {...exporterForm.register('address_line2')}
                  />
                </div>

                <div>
                  <Label htmlFor="exporter_address_line3">Address Line 3</Label>
                  <Input
                    id="exporter_address_line3"
                    placeholder="Country"
                    maxLength={255}
                    {...exporterForm.register('address_line3')}
                  />
                </div>

                <div className="flex gap-2 pt-4">
                  <Button type="submit" disabled={createMutation.isPending}>
                    <Save className="h-4 w-4 mr-2" />
                    {createMutation.isPending
                      ? 'Creating...'
                      : 'Create Exporter'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.push('/companies')}
                    disabled={createMutation.isPending}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
