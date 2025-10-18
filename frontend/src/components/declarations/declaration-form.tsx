/**
 * Declaration Form Component
 *
 * Form for creating/editing customs declarations
 */

'use client'

import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// Zod schema for validation
const declarationSchema = z.object({
  importerName: z.string().min(1, 'Importer name is required').max(255),
  importerAddress: z.string().min(1, 'Importer address is required'),
  totalValue: z.number().positive('Total value must be positive'),
  currency: z.enum(['USD', 'EUR', 'GBP', 'CNY'], {
    errorMap: () => ({ message: 'Please select a valid currency' })
  })
})

export type DeclarationFormData = z.infer<typeof declarationSchema>

interface DeclarationFormProps {
  initialData?: Partial<DeclarationFormData>
  onSubmit: (data: DeclarationFormData) => void
  isSubmitting?: boolean
}

export function DeclarationForm({
  initialData,
  onSubmit,
  isSubmitting = false
}: DeclarationFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<DeclarationFormData>({
    resolver: zodResolver(declarationSchema),
    defaultValues: initialData
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="importerName" className="block text-sm font-medium">
          Importer Name *
        </label>
        <input
          {...register('importerName')}
          id="importerName"
          type="text"
          className="mt-1 block w-full rounded border p-2"
          aria-invalid={errors.importerName ? 'true' : 'false'}
          aria-describedby={errors.importerName ? 'importerName-error' : undefined}
        />
        {errors.importerName && (
          <p id="importerName-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.importerName.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="importerAddress" className="block text-sm font-medium">
          Importer Address *
        </label>
        <textarea
          {...register('importerAddress')}
          id="importerAddress"
          rows={3}
          className="mt-1 block w-full rounded border p-2"
          aria-invalid={errors.importerAddress ? 'true' : 'false'}
          aria-describedby={errors.importerAddress ? 'importerAddress-error' : undefined}
        />
        {errors.importerAddress && (
          <p id="importerAddress-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.importerAddress.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="totalValue" className="block text-sm font-medium">
          Total Value *
        </label>
        <input
          {...register('totalValue', { valueAsNumber: true })}
          id="totalValue"
          type="number"
          step="0.01"
          className="mt-1 block w-full rounded border p-2"
          aria-invalid={errors.totalValue ? 'true' : 'false'}
          aria-describedby={errors.totalValue ? 'totalValue-error' : undefined}
        />
        {errors.totalValue && (
          <p id="totalValue-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.totalValue.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="currency" className="block text-sm font-medium">
          Currency *
        </label>
        <select
          {...register('currency')}
          id="currency"
          className="mt-1 block w-full rounded border p-2"
          aria-invalid={errors.currency ? 'true' : 'false'}
          aria-describedby={errors.currency ? 'currency-error' : undefined}
        >
          <option value="">Select currency</option>
          <option value="USD">USD - US Dollar</option>
          <option value="EUR">EUR - Euro</option>
          <option value="GBP">GBP - British Pound</option>
          <option value="CNY">CNY - Chinese Yuan</option>
        </select>
        {errors.currency && (
          <p id="currency-error" className="mt-1 text-sm text-red-600" role="alert">
            {errors.currency.message}
          </p>
        )}
      </div>

      <div className="flex justify-end gap-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Declaration'}
        </button>
      </div>
    </form>
  )
}
