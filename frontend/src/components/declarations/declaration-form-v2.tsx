/**
 * Declaration Form Component V2 (Story 3.6 Expansion)
 *
 * Complete form with 12 sections and 77 fields matching VietnameseDeclarationData schema
 * - Confidence indicators with color-coding
 * - Null field placeholders
 * - Section completion tracking
 * - Inline correction flagging
 * - Auto-save every 5 seconds
 * - React Hook Form + Zod validation
 */

'use client'

import React from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Collapsible, CollapsibleContent } from '@/components/ui/collapsible'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-react'
import type { DraftData, LinkedCompanySummary } from '@/types/declaration'
import { ConfidenceInput } from './confidence-input'
import { FieldFlagButton } from './field-flag-button'
import { CompletionBadge } from './completion-badge'
import { CompanyBadge } from './company-badge'
import { getFieldConfidence } from '@/lib/confidence-utils'
import type { SourceMetadataMap } from '@/lib/jump-navigation'
import { SourceMetadataProvider } from './source-metadata-context'

// ==================== Zod Validation Schema ====================

const productLineItemSchema = z.object({
  item_number: z.number().optional().nullable(),
  hs_code: z.string().optional().nullable(),
  product_description: z.string().optional().nullable(),
  quantity_1: z.number().optional().nullable(),
  quantity_unit_1: z.string().optional().nullable(),
  quantity_2: z.number().optional().nullable(),
  quantity_unit_2: z.string().optional().nullable(),
  invoice_unit_price: z.number().optional().nullable(),
  invoice_unit_price_currency: z.string().optional().nullable(),
  invoice_line_total: z.number().optional().nullable(),
  taxable_value_vnd: z.number().optional().nullable(),
  unit_price_vnd: z.number().optional().nullable(),
  country_of_origin_code: z.string().optional().nullable(),
  country_of_origin_name: z.string().optional().nullable(),
  preferential_code: z.string().optional().nullable(),
  manufacturer_name: z.string().optional().nullable(),
  brand_name: z.string().optional().nullable(),
  condition: z.string().optional().nullable(),
})

const declarationFormSchema = z.object({
  declaration_header: z
    .object({
      declaration_number: z.string().optional().nullable(),
      declaration_type_code: z.string().optional().nullable(),
      customs_office_code: z.string().optional().nullable(),
      processing_division_code: z.string().optional().nullable(),
      registration_date: z.string().optional().nullable(),
      representative_hs_code: z.string().optional().nullable(),
    })
    .optional(),
  importer: z
    .object({
      tax_code: z.string().optional().nullable(),
      name: z.string().optional().nullable(),
      postal_code: z.string().optional().nullable(),
      address: z.string().optional().nullable(),
      phone: z.string().optional().nullable(),
    })
    .optional(),
  exporter: z
    .object({
      name: z.string().optional().nullable(),
      address_line1: z.string().optional().nullable(),
      address_line2: z.string().optional().nullable(),
      address_line3: z.string().optional().nullable(),
      country_code: z.string().optional().nullable(),
    })
    .optional(),
  shipping_transport: z
    .object({
      bill_of_lading_number: z.string().optional().nullable(),
      warehouse_code: z.string().optional().nullable(),
      warehouse_name: z.string().optional().nullable(),
      port_of_discharge_code: z.string().optional().nullable(),
      port_of_discharge_name: z.string().optional().nullable(),
      port_of_loading_code: z.string().optional().nullable(),
      port_of_loading_name: z.string().optional().nullable(),
      transport_mode_code: z.string().optional().nullable(),
      vessel_name: z.string().optional().nullable(),
      arrival_date: z.string().optional().nullable(),
    })
    .optional(),
  package_container: z
    .object({
      total_packages: z.number().optional().nullable(),
      package_unit: z.string().optional().nullable(),
      package_marks: z.string().optional().nullable(),
      gross_weight_kg: z.number().optional().nullable(),
      gross_weight_unit: z.string().optional().nullable(),
      container_count: z.number().optional().nullable(),
    })
    .optional(),
  invoice: z
    .object({
      invoice_number: z.string().optional().nullable(),
      invoice_date: z.string().optional().nullable(),
      payment_method_code: z.string().optional().nullable(),
      invoice_total: z.number().optional().nullable(),
      invoice_currency: z.string().optional().nullable(),
      invoice_incoterm: z.string().optional().nullable(),
      total_taxable_value_vnd: z.number().optional().nullable(),
      exchange_rate: z.number().optional().nullable(),
    })
    .optional(),
  certificate_of_origin: z
    .object({
      co_form_type: z.string().optional().nullable(),
      co_number: z.string().optional().nullable(),
      co_date: z.string().optional().nullable(),
    })
    .optional(),
  products: z.array(productLineItemSchema).optional(),
  import_duty: z
    .object({
      rate: z.number().optional().nullable(),
      rate_type: z.string().optional().nullable(),
      amount: z.number().optional().nullable(),
      exemption_amount: z.number().optional().nullable(),
    })
    .optional(),
  vat: z
    .object({
      name: z.string().optional().nullable(),
      rate_code: z.string().optional().nullable(),
      rate: z.number().optional().nullable(),
      taxable_value_vnd: z.number().optional().nullable(),
      amount: z.number().optional().nullable(),
      exemption_amount: z.number().optional().nullable(),
    })
    .optional(),
  tax_summary: z
    .object({
      total_tax_amount_vnd: z.number().optional().nullable(),
      tax_payment_deadline_code: z.string().optional().nullable(),
      taxpayer_type: z.string().optional().nullable(),
      tax_classification: z.string().optional().nullable(),
    })
    .optional(),
  metadata: z
    .object({
      total_pages: z.number().optional().nullable(),
      total_line_items: z.number().optional().nullable(),
    })
    .optional(),
})

export type DeclarationFormData = z.infer<typeof declarationFormSchema>

interface DeclarationFormV2Props {
  declarationId: string
  initialData?: DraftData | null
  extractedData?: DraftData | null // Original AI-extracted data for flag button
  confidenceScores?: Record<string, number>
  onSubmit?: (data: DeclarationFormData) => void
  onChange?: (data: DeclarationFormData) => void
  isSubmitting?: boolean
  importerId?: string | null // Story 3.10: Master data link
  exporterId?: string | null // Story 3.10: Master data link
  importerDeclarationCount?: number // Story 3.10: For badge display
  exporterDeclarationCount?: number // Story 3.10: For badge display
  sourceMetadata?: SourceMetadataMap | null
  importerSummary?: LinkedCompanySummary | null
  exporterSummary?: LinkedCompanySummary | null
}

// Helper to count completed fields in a section
function countCompletedFields(
  obj: Record<string, unknown>,
  fieldList: string[]
): { completed: number; total: number } {
  let completed = 0
  fieldList.forEach((field) => {
    const value = obj?.[field]
    if (value !== null && value !== undefined && value !== '') {
      completed++
    }
  })
  return { completed, total: fieldList.length }
}

export function DeclarationFormV2({
  declarationId,
  // initialData is kept in props for API compatibility but not used in this component
  initialData: _initialData, // eslint-disable-line @typescript-eslint/no-unused-vars
  extractedData,
  importerId,
  exporterId,
  importerDeclarationCount,
  exporterDeclarationCount,
  confidenceScores = {},
  onSubmit,
  onChange,
  isSubmitting = false,
  sourceMetadata = null,
  importerSummary = null,
  exporterSummary = null,
}: DeclarationFormV2Props) {
  const [openSections, setOpenSections] = React.useState<Set<string>>(
    new Set(['declaration_header']) // Only Declaration Header open by default
  )

  const { register, handleSubmit, control, watch } =
    useForm<DeclarationFormData>({
      resolver: zodResolver(declarationFormSchema),
      defaultValues: (extractedData as Partial<DeclarationFormData>) || {},
    })

  const {
    fields: productFields,
    append: appendProduct,
    remove: removeProduct,
  } = useFieldArray({
    control,
    name: 'products',
  })

  // Watch all form values for onChange callback and completion tracking
  const formValues = watch()

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

  // Section completion calculations
  const declarationHeaderCompletion = countCompletedFields(
    formValues.declaration_header || {},
    [
      'declaration_type_code',
      'customs_office_code',
      'processing_division_code',
      'registration_date',
      'representative_hs_code',
    ]
  )

  const importerCompletion = countCompletedFields(formValues.importer || {}, [
    'tax_code',
    'name',
    'postal_code',
    'address',
    'phone',
  ])

  const exporterCompletion = countCompletedFields(formValues.exporter || {}, [
    'name',
    'address_line1',
    'address_line2',
    'address_line3',
    'country_code',
  ])

  const shippingTransportCompletion = countCompletedFields(
    formValues.shipping_transport || {},
    [
      'bill_of_lading_number',
      'warehouse_code',
      'warehouse_name',
      'port_of_discharge_code',
      'port_of_discharge_name',
      'port_of_loading_code',
      'port_of_loading_name',
      'transport_mode_code',
      'vessel_name',
      'arrival_date',
    ]
  )

  const packageContainerCompletion = countCompletedFields(
    formValues.package_container || {},
    [
      'total_packages',
      'package_unit',
      'package_marks',
      'gross_weight_kg',
      'gross_weight_unit',
      'container_count',
    ]
  )

  const invoiceCompletion = countCompletedFields(formValues.invoice || {}, [
    'invoice_number',
    'invoice_date',
    'payment_method_code',
    'invoice_total',
    'invoice_currency',
    'invoice_incoterm',
    'total_taxable_value_vnd',
    'exchange_rate',
  ])

  const certificateOfOriginCompletion = countCompletedFields(
    formValues.certificate_of_origin || {},
    ['co_form_type', 'co_number', 'co_date']
  )

  const importDutyCompletion = countCompletedFields(
    formValues.import_duty || {},
    ['rate', 'rate_type', 'amount', 'exemption_amount']
  )

  const vatCompletion = countCompletedFields(formValues.vat || {}, [
    'name',
    'rate_code',
    'rate',
    'taxable_value_vnd',
    'amount',
    'exemption_amount',
  ])

  const taxSummaryCompletion = countCompletedFields(
    formValues.tax_summary || {},
    [
      'total_tax_amount_vnd',
      'tax_payment_deadline_code',
      'taxpayer_type',
      'tax_classification',
    ]
  )

  return (
    <SourceMetadataProvider value={sourceMetadata}>
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        {/* Section 1: Declaration Header */}
        <Collapsible open={openSections.has('declaration_header')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('declaration_header')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Declaration Header
                  <CompletionBadge
                    completed={declarationHeaderCompletion.completed}
                    total={declarationHeaderCompletion.total}
                  />
                </CardTitle>
                {openSections.has('declaration_header') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Declaration Number (Read-only)</Label>
                    <ConfidenceInput
                      {...register('declaration_header.declaration_number')}
                      value={formValues.declaration_header?.declaration_number}
                      disabled
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'declaration_header.declaration_number'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Declaration Type Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="declaration_header.declaration_type_code"
                        originalValue={
                          extractedData?.declaration_header
                            ?.declaration_type_code
                        }
                        correctedValue={
                          formValues.declaration_header?.declaration_type_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('declaration_header.declaration_type_code')}
                      value={
                        formValues.declaration_header?.declaration_type_code
                      }
                      placeholder="e.g., A11 2 [4]"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'declaration_header.declaration_type_code'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Customs Office Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="declaration_header.customs_office_code"
                        originalValue={
                          extractedData?.declaration_header?.customs_office_code
                        }
                        correctedValue={
                          formValues.declaration_header?.customs_office_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('declaration_header.customs_office_code')}
                      value={formValues.declaration_header?.customs_office_code}
                      placeholder="e.g., HQHOALAC"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'declaration_header.customs_office_code'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Processing Division Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="declaration_header.processing_division_code"
                        originalValue={
                          extractedData?.declaration_header
                            ?.processing_division_code
                        }
                        correctedValue={
                          formValues.declaration_header
                            ?.processing_division_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register(
                        'declaration_header.processing_division_code'
                      )}
                      value={
                        formValues.declaration_header?.processing_division_code
                      }
                      placeholder="e.g., 00"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'declaration_header.processing_division_code'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Registration Date</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="declaration_header.registration_date"
                        originalValue={
                          extractedData?.declaration_header?.registration_date
                        }
                        correctedValue={
                          formValues.declaration_header?.registration_date
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('declaration_header.registration_date')}
                      value={formValues.declaration_header?.registration_date}
                      placeholder="DD/MM/YYYY"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'declaration_header.registration_date'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Representative HS Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="declaration_header.representative_hs_code"
                        originalValue={
                          extractedData?.declaration_header
                            ?.representative_hs_code
                        }
                        correctedValue={
                          formValues.declaration_header?.representative_hs_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('declaration_header.representative_hs_code')}
                      value={
                        formValues.declaration_header?.representative_hs_code
                      }
                      placeholder="First 4 digits"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'declaration_header.representative_hs_code'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 2: Importer Information */}
        <Collapsible open={openSections.has('importer')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('importer')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Importer Information
                  <CompletionBadge
                    completed={importerCompletion.completed}
                    total={importerCompletion.total}
                  />
                  <CompanyBadge
                    isVerified={Boolean(
                      importerSummary?.is_verified ?? importerId
                    )}
                    declarationCount={
                      importerSummary?.declaration_count ??
                      importerDeclarationCount
                    }
                  />
                </CardTitle>
                {openSections.has('importer') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Tax Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="importer.tax_code"
                        originalValue={extractedData?.importer?.tax_code}
                        correctedValue={formValues.importer?.tax_code}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('importer.tax_code')}
                      value={formValues.importer?.tax_code}
                      placeholder="10-digit tax ID"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'importer.tax_code'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Name</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="importer.name"
                        originalValue={extractedData?.importer?.name}
                        correctedValue={formValues.importer?.name}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('importer.name')}
                      value={formValues.importer?.name}
                      placeholder="Full legal name"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'importer.name'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Postal Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="importer.postal_code"
                        originalValue={extractedData?.importer?.postal_code}
                        correctedValue={formValues.importer?.postal_code}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('importer.postal_code')}
                      value={formValues.importer?.postal_code}
                      placeholder="Postal code"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'importer.postal_code'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Phone</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="importer.phone"
                        originalValue={extractedData?.importer?.phone}
                        correctedValue={formValues.importer?.phone}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('importer.phone')}
                      value={formValues.importer?.phone}
                      placeholder="Phone number"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'importer.phone'
                      )}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center">
                    <Label>Address</Label>
                    <FieldFlagButton
                      declarationId={declarationId}
                      fieldName="importer.address"
                      originalValue={extractedData?.importer?.address}
                      correctedValue={formValues.importer?.address}
                    />
                  </div>
                  <ConfidenceInput
                    {...register('importer.address')}
                    value={formValues.importer?.address}
                    placeholder="Full address in Vietnam"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'importer.address'
                    )}
                  />
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 3: Exporter Information */}
        <Collapsible open={openSections.has('exporter')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('exporter')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Exporter Information
                  <CompletionBadge
                    completed={exporterCompletion.completed}
                    total={exporterCompletion.total}
                  />
                  <CompanyBadge
                    isVerified={Boolean(
                      exporterSummary?.is_verified ?? exporterId
                    )}
                    declarationCount={
                      exporterSummary?.declaration_count ??
                      exporterDeclarationCount
                    }
                  />
                </CardTitle>
                {openSections.has('exporter') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center">
                    <Label>Name</Label>
                    <FieldFlagButton
                      declarationId={declarationId}
                      fieldName="exporter.name"
                      originalValue={extractedData?.exporter?.name}
                      correctedValue={formValues.exporter?.name}
                    />
                  </div>
                  <ConfidenceInput
                    {...register('exporter.name')}
                    value={formValues.exporter?.name}
                    placeholder="Full legal name of exporter"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'exporter.name'
                    )}
                  />
                </div>

                <div>
                  <div className="flex items-center">
                    <Label>Address Line 1</Label>
                    <FieldFlagButton
                      declarationId={declarationId}
                      fieldName="exporter.address_line1"
                      originalValue={extractedData?.exporter?.address_line1}
                      correctedValue={formValues.exporter?.address_line1}
                    />
                  </div>
                  <ConfidenceInput
                    {...register('exporter.address_line1')}
                    value={formValues.exporter?.address_line1}
                    placeholder="Primary address line"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'exporter.address_line1'
                    )}
                  />
                </div>

                <div>
                  <div className="flex items-center">
                    <Label>Address Line 2</Label>
                    <FieldFlagButton
                      declarationId={declarationId}
                      fieldName="exporter.address_line2"
                      originalValue={extractedData?.exporter?.address_line2}
                      correctedValue={formValues.exporter?.address_line2}
                    />
                  </div>
                  <ConfidenceInput
                    {...register('exporter.address_line2')}
                    value={formValues.exporter?.address_line2}
                    placeholder="Additional address line"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'exporter.address_line2'
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Address Line 3</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="exporter.address_line3"
                        originalValue={extractedData?.exporter?.address_line3}
                        correctedValue={formValues.exporter?.address_line3}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('exporter.address_line3')}
                      value={formValues.exporter?.address_line3}
                      placeholder="City, province, country"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'exporter.address_line3'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Country Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="exporter.country_code"
                        originalValue={extractedData?.exporter?.country_code}
                        correctedValue={formValues.exporter?.country_code}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('exporter.country_code')}
                      value={formValues.exporter?.country_code}
                      placeholder="e.g., CN, US"
                      maxLength={2}
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'exporter.country_code'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 4: Shipping & Transport */}
        <Collapsible open={openSections.has('shipping_transport')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('shipping_transport')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Shipping & Transport
                  <CompletionBadge
                    completed={shippingTransportCompletion.completed}
                    total={shippingTransportCompletion.total}
                  />
                </CardTitle>
                {openSections.has('shipping_transport') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Bill of Lading Number</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.bill_of_lading_number"
                        originalValue={
                          extractedData?.shipping_transport
                            ?.bill_of_lading_number
                        }
                        correctedValue={
                          formValues.shipping_transport?.bill_of_lading_number
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.bill_of_lading_number')}
                      value={
                        formValues.shipping_transport?.bill_of_lading_number
                      }
                      placeholder="B/L or AWB number"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.bill_of_lading_number'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Warehouse Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.warehouse_code"
                        originalValue={
                          extractedData?.shipping_transport?.warehouse_code
                        }
                        correctedValue={
                          formValues.shipping_transport?.warehouse_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.warehouse_code')}
                      value={formValues.shipping_transport?.warehouse_code}
                      placeholder="Warehouse/CFS code"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.warehouse_code'
                      )}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center">
                    <Label>Warehouse Name</Label>
                    <FieldFlagButton
                      declarationId={declarationId}
                      fieldName="shipping_transport.warehouse_name"
                      originalValue={
                        extractedData?.shipping_transport?.warehouse_name
                      }
                      correctedValue={
                        formValues.shipping_transport?.warehouse_name
                      }
                    />
                  </div>
                  <ConfidenceInput
                    {...register('shipping_transport.warehouse_name')}
                    value={formValues.shipping_transport?.warehouse_name}
                    placeholder="Warehouse name"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'shipping_transport.warehouse_name'
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Port of Discharge Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.port_of_discharge_code"
                        originalValue={
                          extractedData?.shipping_transport
                            ?.port_of_discharge_code
                        }
                        correctedValue={
                          formValues.shipping_transport?.port_of_discharge_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.port_of_discharge_code')}
                      value={
                        formValues.shipping_transport?.port_of_discharge_code
                      }
                      placeholder="UN/LOCODE"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.port_of_discharge_code'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Port of Discharge Name</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.port_of_discharge_name"
                        originalValue={
                          extractedData?.shipping_transport
                            ?.port_of_discharge_name
                        }
                        correctedValue={
                          formValues.shipping_transport?.port_of_discharge_name
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.port_of_discharge_name')}
                      value={
                        formValues.shipping_transport?.port_of_discharge_name
                      }
                      placeholder="Port name"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.port_of_discharge_name'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Port of Loading Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.port_of_loading_code"
                        originalValue={
                          extractedData?.shipping_transport
                            ?.port_of_loading_code
                        }
                        correctedValue={
                          formValues.shipping_transport?.port_of_loading_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.port_of_loading_code')}
                      value={
                        formValues.shipping_transport?.port_of_loading_code
                      }
                      placeholder="UN/LOCODE"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.port_of_loading_code'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Port of Loading Name</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.port_of_loading_name"
                        originalValue={
                          extractedData?.shipping_transport
                            ?.port_of_loading_name
                        }
                        correctedValue={
                          formValues.shipping_transport?.port_of_loading_name
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.port_of_loading_name')}
                      value={
                        formValues.shipping_transport?.port_of_loading_name
                      }
                      placeholder="Port name"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.port_of_loading_name'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Transport Mode Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.transport_mode_code"
                        originalValue={
                          extractedData?.shipping_transport?.transport_mode_code
                        }
                        correctedValue={
                          formValues.shipping_transport?.transport_mode_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.transport_mode_code')}
                      value={formValues.shipping_transport?.transport_mode_code}
                      placeholder="e.g., 9999"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.transport_mode_code'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Vessel Name</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.vessel_name"
                        originalValue={
                          extractedData?.shipping_transport?.vessel_name
                        }
                        correctedValue={
                          formValues.shipping_transport?.vessel_name
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.vessel_name')}
                      value={formValues.shipping_transport?.vessel_name}
                      placeholder="Vessel name and voyage"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.vessel_name'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Arrival Date</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="shipping_transport.arrival_date"
                        originalValue={
                          extractedData?.shipping_transport?.arrival_date
                        }
                        correctedValue={
                          formValues.shipping_transport?.arrival_date
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('shipping_transport.arrival_date')}
                      value={formValues.shipping_transport?.arrival_date}
                      placeholder="DD/MM/YYYY"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'shipping_transport.arrival_date'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 5: Package & Container */}
        <Collapsible open={openSections.has('package_container')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('package_container')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Package & Container
                  <CompletionBadge
                    completed={packageContainerCompletion.completed}
                    total={packageContainerCompletion.total}
                  />
                </CardTitle>
                {openSections.has('package_container') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Total Packages</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="package_container.total_packages"
                        originalValue={
                          extractedData?.package_container?.total_packages
                        }
                        correctedValue={
                          formValues.package_container?.total_packages
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('package_container.total_packages', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      value={formValues.package_container?.total_packages}
                      placeholder="Number"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'package_container.total_packages'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Package Unit</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="package_container.package_unit"
                        originalValue={
                          extractedData?.package_container?.package_unit
                        }
                        correctedValue={
                          formValues.package_container?.package_unit
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('package_container.package_unit')}
                      value={formValues.package_container?.package_unit}
                      placeholder="e.g., PK, CT"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'package_container.package_unit'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Container Count</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="package_container.container_count"
                        originalValue={
                          extractedData?.package_container?.container_count
                        }
                        correctedValue={
                          formValues.package_container?.container_count
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('package_container.container_count', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      value={formValues.package_container?.container_count}
                      placeholder="Number"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'package_container.container_count'
                      )}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center">
                    <Label>Package Marks</Label>
                    <FieldFlagButton
                      declarationId={declarationId}
                      fieldName="package_container.package_marks"
                      originalValue={
                        extractedData?.package_container?.package_marks
                      }
                      correctedValue={
                        formValues.package_container?.package_marks
                      }
                    />
                  </div>
                  <ConfidenceInput
                    {...register('package_container.package_marks')}
                    value={formValues.package_container?.package_marks}
                    placeholder="Shipping marks and numbers"
                    confidenceScore={getFieldConfidence(
                      confidenceScores,
                      'package_container.package_marks'
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Gross Weight (kg)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="package_container.gross_weight_kg"
                        originalValue={
                          extractedData?.package_container?.gross_weight_kg
                        }
                        correctedValue={
                          formValues.package_container?.gross_weight_kg
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('package_container.gross_weight_kg', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.package_container?.gross_weight_kg}
                      placeholder="Weight"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'package_container.gross_weight_kg'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Weight Unit</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="package_container.gross_weight_unit"
                        originalValue={
                          extractedData?.package_container?.gross_weight_unit
                        }
                        correctedValue={
                          formValues.package_container?.gross_weight_unit
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('package_container.gross_weight_unit')}
                      value={formValues.package_container?.gross_weight_unit}
                      placeholder="e.g., KGM"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'package_container.gross_weight_unit'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 6: Invoice Details */}
        <Collapsible open={openSections.has('invoice')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('invoice')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Invoice Details
                  <CompletionBadge
                    completed={invoiceCompletion.completed}
                    total={invoiceCompletion.total}
                  />
                </CardTitle>
                {openSections.has('invoice') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Invoice Number</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="invoice.invoice_number"
                        originalValue={extractedData?.invoice?.invoice_number}
                        correctedValue={formValues.invoice?.invoice_number}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('invoice.invoice_number')}
                      value={formValues.invoice?.invoice_number}
                      placeholder="Commercial invoice number"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'invoice.invoice_number'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Invoice Date</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="invoice.invoice_date"
                        originalValue={extractedData?.invoice?.invoice_date}
                        correctedValue={formValues.invoice?.invoice_date}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('invoice.invoice_date')}
                      value={formValues.invoice?.invoice_date}
                      placeholder="DD/MM/YYYY"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'invoice.invoice_date'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Payment Method Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="invoice.payment_method_code"
                        originalValue={
                          extractedData?.invoice?.payment_method_code
                        }
                        correctedValue={formValues.invoice?.payment_method_code}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('invoice.payment_method_code')}
                      value={formValues.invoice?.payment_method_code}
                      placeholder="e.g., KC"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'invoice.payment_method_code'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Invoice Total</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="invoice.invoice_total"
                        originalValue={extractedData?.invoice?.invoice_total}
                        correctedValue={formValues.invoice?.invoice_total}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('invoice.invoice_total', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.invoice?.invoice_total}
                      placeholder="Total value"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'invoice.invoice_total'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Currency</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="invoice.invoice_currency"
                        originalValue={extractedData?.invoice?.invoice_currency}
                        correctedValue={formValues.invoice?.invoice_currency}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('invoice.invoice_currency')}
                      value={formValues.invoice?.invoice_currency}
                      placeholder="e.g., USD"
                      maxLength={3}
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'invoice.invoice_currency'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Incoterm</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="invoice.invoice_incoterm"
                        originalValue={extractedData?.invoice?.invoice_incoterm}
                        correctedValue={formValues.invoice?.invoice_incoterm}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('invoice.invoice_incoterm')}
                      value={formValues.invoice?.invoice_incoterm}
                      placeholder="e.g., FOB, CIF"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'invoice.invoice_incoterm'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Total Taxable Value (VND)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="invoice.total_taxable_value_vnd"
                        originalValue={
                          extractedData?.invoice?.total_taxable_value_vnd
                        }
                        correctedValue={
                          formValues.invoice?.total_taxable_value_vnd
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('invoice.total_taxable_value_vnd', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.invoice?.total_taxable_value_vnd}
                      placeholder="Calculated value"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'invoice.total_taxable_value_vnd'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Exchange Rate</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="invoice.exchange_rate"
                        originalValue={extractedData?.invoice?.exchange_rate}
                        correctedValue={formValues.invoice?.exchange_rate}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('invoice.exchange_rate', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.invoice?.exchange_rate}
                      placeholder="USD to VND rate"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'invoice.exchange_rate'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 7: Certificate of Origin */}
        <Collapsible open={openSections.has('certificate_of_origin')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('certificate_of_origin')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Certificate of Origin
                  <CompletionBadge
                    completed={certificateOfOriginCompletion.completed}
                    total={certificateOfOriginCompletion.total}
                  />
                </CardTitle>
                {openSections.has('certificate_of_origin') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Form Type</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="certificate_of_origin.co_form_type"
                        originalValue={
                          extractedData?.certificate_of_origin?.co_form_type
                        }
                        correctedValue={
                          formValues.certificate_of_origin?.co_form_type
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('certificate_of_origin.co_form_type')}
                      value={formValues.certificate_of_origin?.co_form_type}
                      placeholder="e.g., Form E, Form AK"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'certificate_of_origin.co_form_type'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>C/O Number</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="certificate_of_origin.co_number"
                        originalValue={
                          extractedData?.certificate_of_origin?.co_number
                        }
                        correctedValue={
                          formValues.certificate_of_origin?.co_number
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('certificate_of_origin.co_number')}
                      value={formValues.certificate_of_origin?.co_number}
                      placeholder="Certificate number"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'certificate_of_origin.co_number'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>C/O Date</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="certificate_of_origin.co_date"
                        originalValue={
                          extractedData?.certificate_of_origin?.co_date
                        }
                        correctedValue={
                          formValues.certificate_of_origin?.co_date
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('certificate_of_origin.co_date')}
                      value={formValues.certificate_of_origin?.co_date}
                      placeholder="DD/MM/YYYY"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'certificate_of_origin.co_date'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 8: Product Line Items - CONTINUED IN NEXT PART DUE TO LENGTH */}
        <Collapsible open={openSections.has('products')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('products')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Product Line Items ({productFields.length})
                </CardTitle>
                {openSections.has('products') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent>
                <div className="mb-4 flex justify-end">
                  <Button
                    type="button"
                    size="sm"
                    onClick={() =>
                      appendProduct({
                        item_number: productFields.length + 1,
                        hs_code: null,
                        product_description: null,
                        quantity_1: null,
                        quantity_unit_1: null,
                        quantity_2: null,
                        quantity_unit_2: null,
                        invoice_unit_price: null,
                        invoice_unit_price_currency: null,
                        invoice_line_total: null,
                        taxable_value_vnd: null,
                        unit_price_vnd: null,
                        country_of_origin_code: null,
                        country_of_origin_name: null,
                        preferential_code: null,
                        manufacturer_name: null,
                        brand_name: null,
                        condition: null,
                      })
                    }
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Product
                  </Button>
                </div>

                <div className="space-y-6">
                  {productFields.map((field, index) => (
                    <div
                      key={field.id}
                      className="border rounded-lg p-4 space-y-4 bg-gray-50"
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Product {index + 1}</h4>
                        {productFields.length > 1 && (
                          <Button
                            type="button"
                            size="sm"
                            variant="destructive"
                            onClick={() => removeProduct(index)}
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            Remove
                          </Button>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="flex items-center">
                            <Label>Item Number</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.item_number`}
                              originalValue={
                                extractedData?.products?.[index]?.item_number
                              }
                              correctedValue={
                                formValues.products?.[index]?.item_number
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.item_number`, {
                              valueAsNumber: true,
                            })}
                            type="number"
                            value={formValues.products?.[index]?.item_number}
                            placeholder="Sequential number"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.item_number`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>HS Code (8 digits)</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.hs_code`}
                              originalValue={
                                extractedData?.products?.[index]?.hs_code
                              }
                              correctedValue={
                                formValues.products?.[index]?.hs_code
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.hs_code`)}
                            value={formValues.products?.[index]?.hs_code}
                            placeholder="8 digits"
                            maxLength={8}
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.hs_code`
                            )}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center">
                          <Label>Product Description</Label>
                          <FieldFlagButton
                            declarationId={declarationId}
                            fieldName={`products.${index}.product_description`}
                            originalValue={
                              extractedData?.products?.[index]
                                ?.product_description
                            }
                            correctedValue={
                              formValues.products?.[index]?.product_description
                            }
                          />
                        </div>
                        <ConfidenceInput
                          {...register(`products.${index}.product_description`)}
                          value={
                            formValues.products?.[index]?.product_description
                          }
                          placeholder="Full product description"
                          confidenceScore={getFieldConfidence(
                            confidenceScores,
                            `products.${index}.product_description`
                          )}
                        />
                      </div>

                      <div className="grid grid-cols-4 gap-4">
                        <div>
                          <div className="flex items-center">
                            <Label>Quantity 1</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.quantity_1`}
                              originalValue={
                                extractedData?.products?.[index]?.quantity_1
                              }
                              correctedValue={
                                formValues.products?.[index]?.quantity_1
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.quantity_1`, {
                              valueAsNumber: true,
                            })}
                            type="number"
                            step="0.01"
                            value={formValues.products?.[index]?.quantity_1}
                            placeholder="Primary qty"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.quantity_1`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Unit 1</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.quantity_unit_1`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.quantity_unit_1
                              }
                              correctedValue={
                                formValues.products?.[index]?.quantity_unit_1
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.quantity_unit_1`)}
                            value={
                              formValues.products?.[index]?.quantity_unit_1
                            }
                            placeholder="e.g., PCE, KGM"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.quantity_unit_1`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Quantity 2</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.quantity_2`}
                              originalValue={
                                extractedData?.products?.[index]?.quantity_2
                              }
                              correctedValue={
                                formValues.products?.[index]?.quantity_2
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.quantity_2`, {
                              valueAsNumber: true,
                            })}
                            type="number"
                            step="0.01"
                            value={formValues.products?.[index]?.quantity_2}
                            placeholder="Secondary qty"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.quantity_2`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Unit 2</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.quantity_unit_2`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.quantity_unit_2
                              }
                              correctedValue={
                                formValues.products?.[index]?.quantity_unit_2
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.quantity_unit_2`)}
                            value={
                              formValues.products?.[index]?.quantity_unit_2
                            }
                            placeholder="Unit"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.quantity_unit_2`
                            )}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <div className="flex items-center">
                            <Label>Unit Price</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.invoice_unit_price`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.invoice_unit_price
                              }
                              correctedValue={
                                formValues.products?.[index]?.invoice_unit_price
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(
                              `products.${index}.invoice_unit_price`,
                              {
                                valueAsNumber: true,
                              }
                            )}
                            type="number"
                            step="0.01"
                            value={
                              formValues.products?.[index]?.invoice_unit_price
                            }
                            placeholder="Unit price"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.invoice_unit_price`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Currency</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.invoice_unit_price_currency`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.invoice_unit_price_currency
                              }
                              correctedValue={
                                formValues.products?.[index]
                                  ?.invoice_unit_price_currency
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(
                              `products.${index}.invoice_unit_price_currency`
                            )}
                            value={
                              formValues.products?.[index]
                                ?.invoice_unit_price_currency
                            }
                            placeholder="e.g., USD"
                            maxLength={3}
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.invoice_unit_price_currency`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Line Total</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.invoice_line_total`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.invoice_line_total
                              }
                              correctedValue={
                                formValues.products?.[index]?.invoice_line_total
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(
                              `products.${index}.invoice_line_total`,
                              {
                                valueAsNumber: true,
                              }
                            )}
                            type="number"
                            step="0.01"
                            value={
                              formValues.products?.[index]?.invoice_line_total
                            }
                            placeholder="Total"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.invoice_line_total`
                            )}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="flex items-center">
                            <Label>Taxable Value (VND)</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.taxable_value_vnd`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.taxable_value_vnd
                              }
                              correctedValue={
                                formValues.products?.[index]?.taxable_value_vnd
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(
                              `products.${index}.taxable_value_vnd`,
                              {
                                valueAsNumber: true,
                              }
                            )}
                            type="number"
                            step="0.01"
                            value={
                              formValues.products?.[index]?.taxable_value_vnd
                            }
                            placeholder="Calculated"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.taxable_value_vnd`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Unit Price (VND)</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.unit_price_vnd`}
                              originalValue={
                                extractedData?.products?.[index]?.unit_price_vnd
                              }
                              correctedValue={
                                formValues.products?.[index]?.unit_price_vnd
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.unit_price_vnd`, {
                              valueAsNumber: true,
                            })}
                            type="number"
                            step="0.01"
                            value={formValues.products?.[index]?.unit_price_vnd}
                            placeholder="Calculated"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.unit_price_vnd`
                            )}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="flex items-center">
                            <Label>Country of Origin Code</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.country_of_origin_code`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.country_of_origin_code
                              }
                              correctedValue={
                                formValues.products?.[index]
                                  ?.country_of_origin_code
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(
                              `products.${index}.country_of_origin_code`
                            )}
                            value={
                              formValues.products?.[index]
                                ?.country_of_origin_code
                            }
                            placeholder="e.g., CN, US"
                            maxLength={2}
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.country_of_origin_code`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Country Name</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.country_of_origin_name`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.country_of_origin_name
                              }
                              correctedValue={
                                formValues.products?.[index]
                                  ?.country_of_origin_name
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(
                              `products.${index}.country_of_origin_name`
                            )}
                            value={
                              formValues.products?.[index]
                                ?.country_of_origin_name
                            }
                            placeholder="e.g., CHINA"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.country_of_origin_name`
                            )}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <div className="flex items-center">
                            <Label>Preferential Code</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.preferential_code`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.preferential_code
                              }
                              correctedValue={
                                formValues.products?.[index]?.preferential_code
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.preferential_code`)}
                            value={
                              formValues.products?.[index]?.preferential_code
                            }
                            placeholder="e.g., B05"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.preferential_code`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Manufacturer</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.manufacturer_name`}
                              originalValue={
                                extractedData?.products?.[index]
                                  ?.manufacturer_name
                              }
                              correctedValue={
                                formValues.products?.[index]?.manufacturer_name
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.manufacturer_name`)}
                            value={
                              formValues.products?.[index]?.manufacturer_name
                            }
                            placeholder="Manufacturer name"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.manufacturer_name`
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center">
                            <Label>Brand Name</Label>
                            <FieldFlagButton
                              declarationId={declarationId}
                              fieldName={`products.${index}.brand_name`}
                              originalValue={
                                extractedData?.products?.[index]?.brand_name
                              }
                              correctedValue={
                                formValues.products?.[index]?.brand_name
                              }
                            />
                          </div>
                          <ConfidenceInput
                            {...register(`products.${index}.brand_name`)}
                            value={formValues.products?.[index]?.brand_name}
                            placeholder="Brand/trademark"
                            confidenceScore={getFieldConfidence(
                              confidenceScores,
                              `products.${index}.brand_name`
                            )}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center">
                          <Label>Condition</Label>
                          <FieldFlagButton
                            declarationId={declarationId}
                            fieldName={`products.${index}.condition`}
                            originalValue={
                              extractedData?.products?.[index]?.condition
                            }
                            correctedValue={
                              formValues.products?.[index]?.condition
                            }
                          />
                        </div>
                        <ConfidenceInput
                          {...register(`products.${index}.condition`)}
                          value={formValues.products?.[index]?.condition}
                          placeholder="e.g., Mới 100%"
                          confidenceScore={getFieldConfidence(
                            confidenceScores,
                            `products.${index}.condition`
                          )}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 9: Import Duty */}
        <Collapsible open={openSections.has('import_duty')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('import_duty')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Import Duty
                  <CompletionBadge
                    completed={importDutyCompletion.completed}
                    total={importDutyCompletion.total}
                  />
                </CardTitle>
                {openSections.has('import_duty') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Rate (%)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="import_duty.rate"
                        originalValue={extractedData?.import_duty?.rate}
                        correctedValue={formValues.import_duty?.rate}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('import_duty.rate', { valueAsNumber: true })}
                      type="number"
                      step="0.01"
                      value={formValues.import_duty?.rate}
                      placeholder="Duty rate"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'import_duty.rate'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Rate Type</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="import_duty.rate_type"
                        originalValue={extractedData?.import_duty?.rate_type}
                        correctedValue={formValues.import_duty?.rate_type}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('import_duty.rate_type')}
                      value={formValues.import_duty?.rate_type}
                      placeholder="C, S, or M"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'import_duty.rate_type'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Amount (VND)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="import_duty.amount"
                        originalValue={extractedData?.import_duty?.amount}
                        correctedValue={formValues.import_duty?.amount}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('import_duty.amount', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.import_duty?.amount}
                      placeholder="Calculated amount"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'import_duty.amount'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Exemption Amount (VND)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="import_duty.exemption_amount"
                        originalValue={
                          extractedData?.import_duty?.exemption_amount
                        }
                        correctedValue={
                          formValues.import_duty?.exemption_amount
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('import_duty.exemption_amount', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.import_duty?.exemption_amount}
                      placeholder="Exemption"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'import_duty.exemption_amount'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 10: VAT & Other Taxes */}
        <Collapsible open={openSections.has('vat')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('vat')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  VAT & Other Taxes
                  <CompletionBadge
                    completed={vatCompletion.completed}
                    total={vatCompletion.total}
                  />
                </CardTitle>
                {openSections.has('vat') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Tax Name</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="vat.name"
                        originalValue={extractedData?.vat?.name}
                        correctedValue={formValues.vat?.name}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('vat.name')}
                      value={formValues.vat?.name}
                      placeholder="e.g., Thuế GTGT"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'vat.name'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Rate Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="vat.rate_code"
                        originalValue={extractedData?.vat?.rate_code}
                        correctedValue={formValues.vat?.rate_code}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('vat.rate_code')}
                      value={formValues.vat?.rate_code}
                      placeholder="e.g., VB245"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'vat.rate_code'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Rate (%)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="vat.rate"
                        originalValue={extractedData?.vat?.rate}
                        correctedValue={formValues.vat?.rate}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('vat.rate', { valueAsNumber: true })}
                      type="number"
                      step="0.01"
                      value={formValues.vat?.rate}
                      placeholder="VAT rate"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'vat.rate'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Taxable Value (VND)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="vat.taxable_value_vnd"
                        originalValue={extractedData?.vat?.taxable_value_vnd}
                        correctedValue={formValues.vat?.taxable_value_vnd}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('vat.taxable_value_vnd', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.vat?.taxable_value_vnd}
                      placeholder="Taxable value"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'vat.taxable_value_vnd'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Amount (VND)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="vat.amount"
                        originalValue={extractedData?.vat?.amount}
                        correctedValue={formValues.vat?.amount}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('vat.amount', { valueAsNumber: true })}
                      type="number"
                      step="0.01"
                      value={formValues.vat?.amount}
                      placeholder="VAT amount"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'vat.amount'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Exemption (VND)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="vat.exemption_amount"
                        originalValue={extractedData?.vat?.exemption_amount}
                        correctedValue={formValues.vat?.exemption_amount}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('vat.exemption_amount', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.vat?.exemption_amount}
                      placeholder="Exemption"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'vat.exemption_amount'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 11: Tax Summary */}
        <Collapsible open={openSections.has('tax_summary')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('tax_summary')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle className="flex items-center gap-3">
                  Tax Summary
                  <CompletionBadge
                    completed={taxSummaryCompletion.completed}
                    total={taxSummaryCompletion.total}
                  />
                </CardTitle>
                {openSections.has('tax_summary') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Total Tax Amount (VND)</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="tax_summary.total_tax_amount_vnd"
                        originalValue={
                          extractedData?.tax_summary?.total_tax_amount_vnd
                        }
                        correctedValue={
                          formValues.tax_summary?.total_tax_amount_vnd
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('tax_summary.total_tax_amount_vnd', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      step="0.01"
                      value={formValues.tax_summary?.total_tax_amount_vnd}
                      placeholder="Total taxes"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'tax_summary.total_tax_amount_vnd'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Payment Deadline Code</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="tax_summary.tax_payment_deadline_code"
                        originalValue={
                          extractedData?.tax_summary?.tax_payment_deadline_code
                        }
                        correctedValue={
                          formValues.tax_summary?.tax_payment_deadline_code
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('tax_summary.tax_payment_deadline_code')}
                      value={formValues.tax_summary?.tax_payment_deadline_code}
                      placeholder="e.g., D"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'tax_summary.tax_payment_deadline_code'
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center">
                      <Label>Taxpayer Type</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="tax_summary.taxpayer_type"
                        originalValue={
                          extractedData?.tax_summary?.taxpayer_type
                        }
                        correctedValue={formValues.tax_summary?.taxpayer_type}
                      />
                    </div>
                    <ConfidenceInput
                      {...register('tax_summary.taxpayer_type')}
                      value={formValues.tax_summary?.taxpayer_type}
                      placeholder="e.g., 1"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'tax_summary.taxpayer_type'
                      )}
                    />
                  </div>
                  <div>
                    <div className="flex items-center">
                      <Label>Tax Classification</Label>
                      <FieldFlagButton
                        declarationId={declarationId}
                        fieldName="tax_summary.tax_classification"
                        originalValue={
                          extractedData?.tax_summary?.tax_classification
                        }
                        correctedValue={
                          formValues.tax_summary?.tax_classification
                        }
                      />
                    </div>
                    <ConfidenceInput
                      {...register('tax_summary.tax_classification')}
                      value={formValues.tax_summary?.tax_classification}
                      placeholder="e.g., A"
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'tax_summary.tax_classification'
                      )}
                    />
                  </div>
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        {/* Section 12: Metadata (Read-only) */}
        <Collapsible open={openSections.has('metadata')}>
          <Card>
            <CardHeader>
              <div
                onClick={() => toggleSection('metadata')}
                className="flex w-full items-center justify-between hover:opacity-80 cursor-pointer"
              >
                <CardTitle>Metadata (Read-only)</CardTitle>
                {openSections.has('metadata') ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </div>
            </CardHeader>
            <CollapsibleContent>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Total Pages</Label>
                    <ConfidenceInput
                      {...register('metadata.total_pages', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      value={formValues.metadata?.total_pages}
                      disabled
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'metadata.total_pages'
                      )}
                    />
                  </div>
                  <div>
                    <Label>Total Line Items</Label>
                    <ConfidenceInput
                      {...register('metadata.total_line_items', {
                        valueAsNumber: true,
                      })}
                      type="number"
                      value={formValues.metadata?.total_line_items}
                      disabled
                      confidenceScore={getFieldConfidence(
                        confidenceScores,
                        'metadata.total_line_items'
                      )}
                    />
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
    </SourceMetadataProvider>
  )
}
