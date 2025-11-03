/**
 * Declaration Review Page
 *
 * Full review interface with editable form, confidence indicators, and auto-save
 */

'use client'

import React from 'react'
import { use } from 'react'
import {
  DeclarationForm,
  DeclarationFormData,
} from '@/components/declarations/declaration-form'
import { ValidationWarningsPanel } from '@/components/declarations/validation-warnings'
import { SaveIndicator } from '@/components/declarations/save-indicator'
import { useDeclaration } from '@/hooks/use-declaration'
import { useAutoSave } from '@/hooks/use-auto-save'

interface DeclarationReviewPageProps {
  params: Promise<{ id: string }>
}

export default function DeclarationReviewPage({
  params,
}: DeclarationReviewPageProps) {
  const { id } = use(params)
  const [formData, setFormData] = React.useState<DeclarationFormData | null>(
    null
  )

  // Fetch declaration data
  const {
    declaration,
    isLoading,
    isError,
    error,
    updateDraftData,
    isUpdating,
    isUpdateSuccess,
    isUpdateError,
  } = useDeclaration(id)

  // Auto-save form changes with 5-second debounce
  const autoSave = useAutoSave(formData, {
    key: ['declarations', id],
    saveFn: async (data) => {
      if (data) {
        updateDraftData(data as unknown as Record<string, unknown>)
      }
    },
    debounceMs: 5000,
    enabled: !!formData, // Only enable once we have form data
  })

  // Handle form changes
  const handleFormChange = (data: DeclarationFormData) => {
    setFormData(data)
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-slate-600">Loading declaration...</p>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-red-700 mb-2">
            Error Loading Declaration
          </h2>
          <p className="text-red-600">
            {error?.message || 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  // No data state
  if (!declaration) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-yellow-700 mb-2">
            Declaration Not Found
          </h2>
          <p className="text-yellow-600">
            The requested declaration could not be found.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-6 py-8 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 mb-2">
            Review Declaration
          </h1>
          <p className="text-sm text-slate-600">
            Declaration ID: {declaration.id}
          </p>
          <p className="text-sm text-slate-600">Status: {declaration.status}</p>
        </div>

        {/* Save Indicator */}
        <SaveIndicator
          isSaving={autoSave.isSaving || isUpdating}
          isSuccess={autoSave.isSuccess || isUpdateSuccess}
          isError={autoSave.isError || isUpdateError}
        />
      </div>

      {/* Validation Warnings */}
      {declaration.validation_warnings &&
        declaration.validation_warnings.length > 0 && (
          <div className="mb-6">
            <ValidationWarningsPanel
              warnings={declaration.validation_warnings}
            />
          </div>
        )}

      {/* Declaration Form */}
      <DeclarationForm
        initialData={declaration.draft_data}
        confidenceScores={declaration.confidence_scores}
        onChange={handleFormChange}
        isSubmitting={autoSave.isSaving}
      />

      {/* Footer Actions */}
      <div className="mt-8 flex justify-between items-center border-t pt-6">
        <div className="text-sm text-slate-600">
          {autoSave.isError && (
            <button
              onClick={autoSave.save}
              className="text-blue-600 hover:text-blue-700 underline"
            >
              Retry Save
            </button>
          )}
        </div>
        <div className="flex gap-4">
          <button className="px-6 py-2 border border-slate-300 rounded-md text-slate-700 hover:bg-slate-50">
            Cancel
          </button>
          <button
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            onClick={autoSave.save}
            disabled={autoSave.isSaving}
          >
            Save Now
          </button>
        </div>
      </div>
    </div>
  )
}
