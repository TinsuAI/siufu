/**
 * Declaration Form Component (DEPRECATED)
 *
 * @deprecated This component uses the OLD schema (company_info, shipment_details).
 * Use DeclarationFormV2 instead, which uses the Vietnamese declaration schema.
 *
 * This component is kept for backward compatibility with existing test data only.
 * All new development should use DeclarationFormV2.
 *
 * Comprehensive form for reviewing and editing extracted declaration data
 * with confidence indicators, auto-save, and validation
 */

'use client'

import React from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-react'
import type { DraftData } from '@/types/declaration'
import { ConfidenceInput } from './confidence-input'
import { FieldLabel } from './field-label'
import type { SourceMetadataMap } from '@/lib/jump-navigation'
import { getFieldConfidence } from '@/lib/confidence-utils'

// ==================== Zod Validation Schema ====================

const productLineItemSchema = z.object({
  description: z.string().min(1, 'Product description is required').max(500),
  hs_code: z
    .string()
    .regex(/^\d{8}$/, 'HS Code must be exactly 8 digits')
    .min(8)
    .max(8),
  quantity: z.number().positive('Quantity must be positive'),
  unit: z.string().min(1, 'Unit is required').max(50),
  unit_price: z.number().positive('Unit price must be positive'),
  total_price: z.number().positive('Total price must be positive'),
  origin_country: z.string().min(2, 'Country code required').max(2),
})

const declarationFormSchema = z.object({
  company_info: z.object({
    importer_name: z.string().min(1, 'Importer name is required').max(255),
    tax_id: z.string().min(1, 'Tax ID is required').max(50),
    address: z.string().min(1, 'Address is required').max(500),
    city: z.string().min(1, 'City is required').max(100),
    country: z.string().min(2, 'Country code required').max(2),
    contact_person: z.string().min(1, 'Contact person is required').max(255),
    contact_email: z.string().email('Invalid email format'),
    contact_phone: z.string().min(1, 'Phone number is required').max(50),
  }),
  shipment_details: z.object({
    bol_number: z.string().min(1, 'BOL number is required').max(100),
    arrival_date: z.string().min(1, 'Arrival date is required'),
    port_of_arrival: z.string().min(1, 'Port of arrival is required').max(100),
    port_of_departure: z
      .string()
      .min(1, 'Port of departure is required')
      .max(100),
    container_numbers: z
      .array(z.string().min(1).max(50))
      .min(1, 'At least one container required'),
    vessel_name: z.string().min(1, 'Vessel name is required').max(255),
  }),
  products: z
    .array(productLineItemSchema)
    .min(1, 'At least one product required'),
  tax_calculations: z.object({
    subtotal: z.number().nonnegative('Subtotal cannot be negative'),
    vat_rate: z
      .number()
      .min(0, 'VAT rate cannot be negative')
      .max(100, 'VAT rate cannot exceed 100%'),
    vat_amount: z.number().nonnegative('VAT amount cannot be negative'),
    import_duty_rate: z
      .number()
      .min(0, 'Import duty rate cannot be negative')
      .max(100, 'Import duty rate cannot exceed 100%'),
    import_duty_amount: z
      .number()
      .nonnegative('Import duty amount cannot be negative'),
    total_tax: z.number().nonnegative('Total tax cannot be negative'),
    grand_total: z.number().nonnegative('Grand total cannot be negative'),
  }),
})

export type DeclarationFormData = z.infer<typeof declarationFormSchema>

interface DeclarationFormProps {
  initialData?: DraftData | null
  confidenceScores?: Record<string, number>
  sourceMetadata?: SourceMetadataMap | null // Story 3.7: field_path -> {source, page, bbox}
  onSubmit?: (data: DeclarationFormData) => void
  onChange?: (data: DeclarationFormData) => void
  isSubmitting?: boolean
}

export function DeclarationForm({
  initialData,
  confidenceScores = {}, // Will be used in Task 2 for color-coding
  sourceMetadata = null, // Story 3.7: source metadata for jump navigation (TODO: integrate with FieldLabel)
  onSubmit,
  onChange,
  isSubmitting = false,
}: DeclarationFormProps) {
  const [openSections, setOpenSections] = React.useState<Set<string>>(
    new Set(['company', 'shipment', 'products', 'tax'])
  )

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<DeclarationFormData>({
    resolver: zodResolver(declarationFormSchema),
    defaultValues: (initialData as DeclarationFormData) || {
      company_info: {
        importer_name: '',
        tax_id: '',
        address: '',
        city: '',
        country: '',
        contact_person: '',
        contact_email: '',
        contact_phone: '',
      },
      shipment_details: {
        bol_number: '',
        arrival_date: '',
        port_of_arrival: '',
        port_of_departure: '',
        container_numbers: [''],
        vessel_name: '',
      },
      products: [
        {
          description: '',
          hs_code: '',
          quantity: 0,
          unit: '',
          unit_price: 0,
          total_price: 0,
          origin_country: '',
        },
      ],
      tax_calculations: {
        subtotal: 0,
        vat_rate: 0,
        vat_amount: 0,
        import_duty_rate: 0,
        import_duty_amount: 0,
        total_tax: 0,
        grand_total: 0,
      },
    },
  })

  const {
    fields: productFields,
    append: appendProduct,
    remove: removeProduct,
  } = useFieldArray({
    control,
    name: 'products',
  })

  const {
    fields: containerFields,
    append: appendContainer,
    remove: removeContainer,
  } = useFieldArray({
    control,
    // @ts-expect-error - React Hook Form typing issue with nested arrays
    name: 'shipment_details.container_numbers',
  })

  // Watch all form values for onChange callback
  React.useEffect(() => {
    if (onChange) {
      const subscription = watch((data) => {
        onChange(data as DeclarationFormData)
      })
      return () => subscription.unsubscribe()
    }
  }, [watch, onChange])

  const toggleSection = (section: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev)
      if (next.has(section)) {
        next.delete(section)
      } else {
        next.add(section)
      }
      return next
    })
  }

  const handleFormSubmit = (data: DeclarationFormData) => {
    if (onSubmit) {
      onSubmit(data)
    }
  }

  // Check if there are multiple validation errors
  const hasErrors = Object.keys(errors).length > 0
  const errorCount = Object.keys(errors).flat().length

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Validation Summary - Shows when multiple errors exist */}
      {hasErrors && errorCount > 1 && (
        <Card className="border-red-300 bg-red-50">
          <CardHeader className="pb-3">
            <CardTitle className="text-red-700 text-lg flex items-center gap-2">
              <span>⚠️</span>
              {errorCount} Validation {errorCount === 1 ? 'Error' : 'Errors'}{' '}
              Found
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-600 mb-2">
              Please correct the following errors before submitting:
            </p>
            <ul className="list-disc list-inside space-y-1 text-sm text-red-600">
              {errors.company_info && (
                <li>Company Information section has errors</li>
              )}
              {errors.shipment_details && (
                <li>Shipment Details section has errors</li>
              )}
              {errors.products && (
                <li>Product Line Items section has errors</li>
              )}
              {errors.tax_calculations && (
                <li>Tax Calculations section has errors</li>
              )}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Section 1: Company Information */}
      <Collapsible open={openSections.has('company')}>
        <Card>
          <CardHeader>
            <CollapsibleTrigger
              onClick={() => toggleSection('company')}
              className="flex w-full items-center justify-between hover:opacity-80"
            >
              <CardTitle>Company Information</CardTitle>
              {openSections.has('company') ? (
                <ChevronUp className="h-5 w-5" />
              ) : (
                <ChevronDown className="h-5 w-5" />
              )}
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel
                    htmlFor="importer_name"
                    label="Importer Name *"
                    fieldPath="company_info.importer_name"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('company_info.importer_name')}
                    id="importer_name"
                    placeholder="Enter importer name"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'company_info.importer_name'
                    )}
                  />
                  {errors.company_info?.importer_name && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.company_info.importer_name.message}
                    </p>
                  )}
                </div>
                <div>
                  <FieldLabel
                    htmlFor="tax_id"
                    label="Tax ID *"
                    fieldPath="company_info.tax_id"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('company_info.tax_id')}
                    id="tax_id"
                    placeholder="Enter tax ID"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'company_info.tax_id'
                    )}
                  />
                  {errors.company_info?.tax_id && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.company_info.tax_id.message}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <FieldLabel
                  htmlFor="address"
                  label="Address *"
                  fieldPath="company_info.address"
                  sourceMetadata={sourceMetadata}
                />
                <ConfidenceInput
                  {...register('company_info.address')}
                  id="address"
                  placeholder="Enter address"
                  confidenceScore={getFieldConfidence(
                    confidenceScores,
                    'company_info.address'
                  )}
                />
                {errors.company_info?.address && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.company_info.address.message}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel
                    htmlFor="city"
                    label="City *"
                    fieldPath="company_info.city"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('company_info.city')}
                    id="city"
                    placeholder="Enter city"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'company_info.city'
                    )}
                  />
                  {errors.company_info?.city && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.company_info.city.message}
                    </p>
                  )}
                </div>
                <div>
                  <FieldLabel
                    htmlFor="country"
                    label="Country Code *"
                    fieldPath="company_info.country"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('company_info.country')}
                    id="country"
                    placeholder="e.g., VN, US"
                    maxLength={2}
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'company_info.country'
                    )}
                  />
                  {errors.company_info?.country && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.company_info.country.message}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <FieldLabel
                  htmlFor="contact_person"
                  label="Contact Person *"
                  fieldPath="company_info.contact_person"
                  sourceMetadata={sourceMetadata}
                />
                <ConfidenceInput
                  {...register('company_info.contact_person')}
                  id="contact_person"
                  placeholder="Enter contact person"
                  confidenceScore={getFieldConfidence(
                    confidenceScores,
                    'company_info.contact_person'
                  )}
                />
                {errors.company_info?.contact_person && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.company_info.contact_person.message}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel
                    htmlFor="contact_email"
                    label="Contact Email *"
                    fieldPath="company_info.contact_email"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('company_info.contact_email')}
                    id="contact_email"
                    type="email"
                    placeholder="email@example.com"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'company_info.contact_email'
                    )}
                  />
                  {errors.company_info?.contact_email && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.company_info.contact_email.message}
                    </p>
                  )}
                </div>
                <div>
                  <FieldLabel
                    htmlFor="contact_phone"
                    label="Contact Phone *"
                    fieldPath="company_info.contact_phone"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('company_info.contact_phone')}
                    id="contact_phone"
                    placeholder="Enter phone number"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'company_info.contact_phone'
                    )}
                  />
                  {errors.company_info?.contact_phone && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.company_info.contact_phone.message}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Section 2: Shipment Details */}
      <Collapsible open={openSections.has('shipment')}>
        <Card>
          <CardHeader>
            <CollapsibleTrigger
              onClick={() => toggleSection('shipment')}
              className="flex w-full items-center justify-between hover:opacity-80"
            >
              <CardTitle>Shipment Details</CardTitle>
              {openSections.has('shipment') ? (
                <ChevronUp className="h-5 w-5" />
              ) : (
                <ChevronDown className="h-5 w-5" />
              )}
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel
                    htmlFor="bol_number"
                    label="BOL Number *"
                    fieldPath="shipment_details.bol_number"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('shipment_details.bol_number')}
                    id="bol_number"
                    placeholder="Enter BOL number"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'shipment_details.bol_number'
                    )}
                  />
                  {errors.shipment_details?.bol_number && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.shipment_details.bol_number.message}
                    </p>
                  )}
                </div>
                <div>
                  <FieldLabel
                    htmlFor="arrival_date"
                    label="Arrival Date *"
                    fieldPath="shipment_details.arrival_date"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('shipment_details.arrival_date')}
                    id="arrival_date"
                    type="date"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'shipment_details.arrival_date'
                    )}
                  />
                  {errors.shipment_details?.arrival_date && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.shipment_details.arrival_date.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel
                    htmlFor="port_of_arrival"
                    label="Port of Arrival *"
                    fieldPath="shipment_details.port_of_arrival"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('shipment_details.port_of_arrival')}
                    id="port_of_arrival"
                    placeholder="Enter port of arrival"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'shipment_details.port_of_arrival'
                    )}
                  />
                  {errors.shipment_details?.port_of_arrival && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.shipment_details.port_of_arrival.message}
                    </p>
                  )}
                </div>
                <div>
                  <FieldLabel
                    htmlFor="port_of_departure"
                    label="Port of Departure *"
                    fieldPath="shipment_details.port_of_departure"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('shipment_details.port_of_departure')}
                    id="port_of_departure"
                    placeholder="Enter port of departure"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'shipment_details.port_of_departure'
                    )}
                  />
                  {errors.shipment_details?.port_of_departure && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.shipment_details.port_of_departure.message}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <FieldLabel
                  htmlFor="vessel_name"
                  label="Vessel Name *"
                  fieldPath="shipment_details.vessel_name"
                  sourceMetadata={sourceMetadata}
                />
                <ConfidenceInput
                  {...register('shipment_details.vessel_name')}
                  id="vessel_name"
                  placeholder="Enter vessel name"
                  confidenceScore={getFieldConfidence(
                    confidenceScores,
                    'shipment_details.vessel_name'
                  )}
                />
                {errors.shipment_details?.vessel_name && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.shipment_details.vessel_name.message}
                  </p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Container Numbers *</Label>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => appendContainer('' as any)}
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Container
                  </Button>
                </div>
                <div className="space-y-2">
                  {containerFields.map((field, index) => (
                    <div key={field.id} className="flex gap-2">
                      <Input
                        {...register(
                          `shipment_details.container_numbers.${index}`
                        )}
                        placeholder={`Container ${index + 1}`}
                      />
                      {containerFields.length > 1 && (
                        <Button
                          type="button"
                          size="sm"
                          variant="destructive"
                          onClick={() => removeContainer(index)}
                          aria-label={`Remove container ${index + 1}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
                {errors.shipment_details?.container_numbers && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.shipment_details.container_numbers.message}
                  </p>
                )}
              </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Section 3: Product Line Items */}
      <Collapsible open={openSections.has('products')}>
        <Card>
          <CardHeader>
            <CollapsibleTrigger
              onClick={() => toggleSection('products')}
              className="flex w-full items-center justify-between hover:opacity-80"
            >
              <CardTitle>Product Line Items</CardTitle>
              {openSections.has('products') ? (
                <ChevronUp className="h-5 w-5" />
              ) : (
                <ChevronDown className="h-5 w-5" />
              )}
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent>
              <div className="mb-4 flex justify-end">
                <Button
                  type="button"
                  size="sm"
                  onClick={() =>
                    appendProduct({
                      description: '',
                      hs_code: '',
                      quantity: 0,
                      unit: '',
                      unit_price: 0,
                      total_price: 0,
                      origin_country: '',
                    })
                  }
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Product
                </Button>
              </div>

              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead>HS Code</TableHead>
                      <TableHead>Qty</TableHead>
                      <TableHead>Unit</TableHead>
                      <TableHead>Unit Price</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Origin</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {productFields.map((field, index) => (
                      <TableRow key={field.id}>
                        <TableCell>
                          <ConfidenceInput
                            {...register(`products.${index}.description`)}
                            placeholder="Product description"
                            aria-label={`Product ${index + 1} description`}
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.description`
                            )}
                          />
                          {errors.products?.[index]?.description && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.products[index]?.description?.message}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <ConfidenceInput
                            {...register(`products.${index}.hs_code`)}
                            placeholder="8 digits"
                            maxLength={8}
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.hs_code`
                            )}
                          />
                          {errors.products?.[index]?.hs_code && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.products[index]?.hs_code?.message}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <ConfidenceInput
                            {...register(`products.${index}.quantity`, {
                              valueAsNumber: true,
                            })}
                            type="number"
                            placeholder="0"
                            className="w-20"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.quantity`
                            )}
                          />
                          {errors.products?.[index]?.quantity && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.products[index]?.quantity?.message}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <ConfidenceInput
                            {...register(`products.${index}.unit`)}
                            placeholder="Unit"
                            className="w-20"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.unit`
                            )}
                          />
                          {errors.products?.[index]?.unit && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.products[index]?.unit?.message}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <ConfidenceInput
                            {...register(`products.${index}.unit_price`, {
                              valueAsNumber: true,
                            })}
                            type="number"
                            step="0.01"
                            placeholder="0.00"
                            className="w-24"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.unit_price`
                            )}
                          />
                          {errors.products?.[index]?.unit_price && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.products[index]?.unit_price?.message}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <ConfidenceInput
                            {...register(`products.${index}.total_price`, {
                              valueAsNumber: true,
                            })}
                            type="number"
                            step="0.01"
                            placeholder="0.00"
                            className="w-24"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.total_price`
                            )}
                          />
                          {errors.products?.[index]?.total_price && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.products[index]?.total_price?.message}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <ConfidenceInput
                            {...register(`products.${index}.origin_country`)}
                            placeholder="VN"
                            maxLength={2}
                            className="w-16"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.origin_country`
                            )}
                          />
                          {errors.products?.[index]?.origin_country && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.products[index]?.origin_country?.message}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          {productFields.length > 1 && (
                            <Button
                              type="button"
                              size="sm"
                              variant="destructive"
                              onClick={() => removeProduct(index)}
                              aria-label={`Remove product ${index + 1}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              {errors.products && (
                <p className="mt-2 text-sm text-red-600">
                  {errors.products.message}
                </p>
              )}
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Section 4: Tax Calculations */}
      <Collapsible open={openSections.has('tax')}>
        <Card>
          <CardHeader>
            <CollapsibleTrigger
              onClick={() => toggleSection('tax')}
              className="flex w-full items-center justify-between hover:opacity-80"
            >
              <CardTitle>Tax Calculations</CardTitle>
              {openSections.has('tax') ? (
                <ChevronUp className="h-5 w-5" />
              ) : (
                <ChevronDown className="h-5 w-5" />
              )}
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-4">
              <div>
                <FieldLabel
                  htmlFor="subtotal"
                  label="Subtotal *"
                  fieldPath="tax_calculations.subtotal"
                  sourceMetadata={sourceMetadata}
                />
                <ConfidenceInput
                  {...register('tax_calculations.subtotal', {
                    valueAsNumber: true,
                  })}
                  id="subtotal"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  confidenceScore={getFieldConfidence(
                    confidenceScores,
                    'tax_calculations.subtotal'
                  )}
                />
                {errors.tax_calculations?.subtotal && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.tax_calculations.subtotal.message}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel
                    htmlFor="vat_rate"
                    label="VAT Rate (%) *"
                    fieldPath="tax_calculations.vat_rate"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('tax_calculations.vat_rate', {
                      valueAsNumber: true,
                    })}
                    id="vat_rate"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'tax_calculations.vat_rate'
                    )}
                  />
                  {errors.tax_calculations?.vat_rate && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.tax_calculations.vat_rate.message}
                    </p>
                  )}
                </div>
                <div>
                  <FieldLabel
                    htmlFor="vat_amount"
                    label="VAT Amount *"
                    fieldPath="tax_calculations.vat_amount"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('tax_calculations.vat_amount', {
                      valueAsNumber: true,
                    })}
                    id="vat_amount"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'tax_calculations.vat_amount'
                    )}
                  />
                  {errors.tax_calculations?.vat_amount && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.tax_calculations.vat_amount.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel
                    htmlFor="import_duty_rate"
                    label="Import Duty Rate (%) *"
                    fieldPath="tax_calculations.import_duty_rate"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('tax_calculations.import_duty_rate', {
                      valueAsNumber: true,
                    })}
                    id="import_duty_rate"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'tax_calculations.import_duty_rate'
                    )}
                  />
                  {errors.tax_calculations?.import_duty_rate && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.tax_calculations.import_duty_rate.message}
                    </p>
                  )}
                </div>
                <div>
                  <FieldLabel
                    htmlFor="import_duty_amount"
                    label="Import Duty Amount *"
                    fieldPath="tax_calculations.import_duty_amount"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('tax_calculations.import_duty_amount', {
                      valueAsNumber: true,
                    })}
                    id="import_duty_amount"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'tax_calculations.import_duty_amount'
                    )}
                  />
                  {errors.tax_calculations?.import_duty_amount && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.tax_calculations.import_duty_amount.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <FieldLabel
                    htmlFor="total_tax"
                    label="Total Tax *"
                    fieldPath="tax_calculations.total_tax"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('tax_calculations.total_tax', {
                      valueAsNumber: true,
                    })}
                    id="total_tax"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'tax_calculations.total_tax'
                    )}
                  />
                  {errors.tax_calculations?.total_tax && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.tax_calculations.total_tax.message}
                    </p>
                  )}
                </div>
                <div>
                  <FieldLabel
                    htmlFor="grand_total"
                    label="Grand Total *"
                    fieldPath="tax_calculations.grand_total"
                    sourceMetadata={sourceMetadata}
                  />
                  <ConfidenceInput
                    {...register('tax_calculations.grand_total', {
                      valueAsNumber: true,
                    })}
                    id="grand_total"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'tax_calculations.grand_total'
                    )}
                  />
                  {errors.tax_calculations?.grand_total && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.tax_calculations.grand_total.message}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Submit Button (Optional) */}
      {onSubmit && (
        <div className="flex justify-end">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Save Declaration'}
          </Button>
        </div>
      )}
    </form>
  )
}
