/**
 * Declaration Review Page
 *
 * Full review interface with editable form, confidence indicators, auto-save,
 * and approve/reject/export functionality
 */

'use client'

import React, { useState, useEffect } from 'react'
import { use } from 'react'
import { useRouter } from 'next/navigation'
import {
  DeclarationFormV2,
  DeclarationFormData,
} from '@/components/declarations/declaration-form-v2'
import { CorrectionsLogPanel } from '@/components/declarations/corrections-log-panel'
import { ValidationWarningsPanel } from '@/components/declarations/validation-warnings'
import { SaveIndicator } from '@/components/declarations/save-indicator'
import { useDeclaration } from '@/hooks/use-declaration'
import { useAutoSave } from '@/hooks/use-auto-save'
import { useToast } from '@/hooks/use-toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Download } from 'lucide-react'

interface DeclarationReviewPageProps {
  params: Promise<{ id: string }>
}

export default function DeclarationReviewPage({
  params,
}: DeclarationReviewPageProps) {
  const { id } = use(params)
  const router = useRouter()
  const { toast } = useToast()
  const [formData, setFormData] = React.useState<DeclarationFormData | null>(
    null
  )
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false)
  const [rejectionReason, setRejectionReason] = useState('')

  // Fetch declaration data and get mutations
  const {
    declaration,
    isLoading,
    isError,
    error,
    updateDraftData,
    isUpdating,
    isUpdateSuccess,
    isUpdateError,
    approveDeclaration: approve,
    isApproving,
    isApproveSuccess,
    isApproveError,
    rejectDeclaration: reject,
    isRejecting,
    isRejectSuccess,
    isRejectError,
    exportDeclarationToExcel: exportExcel,
    isExporting,
    isExportSuccess,
    isExportError,
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

  // Handle approve button click
  const handleApprove = () => {
    approve()
  }

  // Handle reject button click
  const handleRejectClick = () => {
    setRejectDialogOpen(true)
  }

  // Handle reject confirmation
  const handleRejectConfirm = () => {
    if (rejectionReason.trim().length < 10) {
      toast({
        title: 'Invalid Reason',
        description: 'Rejection reason must be at least 10 characters.',
        variant: 'error',
      })
      return
    }

    reject(rejectionReason)
  }

  // Handle download Excel button click
  const handleDownload = () => {
    exportExcel()
  }

  // Show success toast on approval
  useEffect(() => {
    if (isApproveSuccess) {
      toast({
        title: 'Success',
        description: 'Declaration approved successfully',
        variant: 'success',
      })
    }
  }, [isApproveSuccess, toast])

  // Show success toast on rejection and redirect
  useEffect(() => {
    if (isRejectSuccess) {
      toast({
        title: 'Success',
        description: 'Declaration rejected. Reason recorded.',
        variant: 'success',
      })
      setRejectDialogOpen(false)
      // Redirect to declarations list after 1 second
      setTimeout(() => {
        router.push('/declarations')
      }, 1000)
    }
  }, [isRejectSuccess, toast, router])

  // Show success message on export
  useEffect(() => {
    if (isExportSuccess) {
      toast({
        title: 'Success',
        description: 'Declaration approved and exported successfully',
        variant: 'success',
      })
    }
  }, [isExportSuccess, toast])

  // Show error toasts
  useEffect(() => {
    if (isApproveError) {
      toast({
        title: 'Approval Failed',
        description: 'Failed to approve declaration. Please try again.',
        variant: 'error',
      })
    }
  }, [isApproveError, toast])

  useEffect(() => {
    if (isRejectError) {
      toast({
        title: 'Rejection Failed',
        description: 'Failed to reject declaration. Please try again.',
        variant: 'error',
      })
    }
  }, [isRejectError, toast])

  useEffect(() => {
    if (isExportError) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export declaration. Please try again.',
        variant: 'error',
      })
    }
  }, [isExportError, toast])

  // Check if approve button should be disabled
  const isApproveBtnDisabled = autoSave.isSaving || isUpdating || isApproving
  const isApproved = declaration?.status === 'APPROVED'

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
    <TooltipProvider>
      <div className="min-h-screen">
        {/* Sticky Header with Approve/Reject Buttons */}
        <div className="sticky top-0 z-10 bg-white shadow-md border-b border-slate-200">
          <div className="container mx-auto px-6 py-4 max-w-7xl">
            <div className="flex items-center justify-between">
              {/* Left: Title and Info */}
              <div>
                <h1 className="text-2xl font-bold text-slate-800">
                  Review Declaration
                </h1>
                <p className="text-sm text-slate-600">
                  ID: {declaration.id} • Status: {declaration.status}
                </p>
              </div>

              {/* Right: Save Indicator and Action Buttons */}
              <div className="flex items-center gap-4">
                <SaveIndicator
                  isSaving={autoSave.isSaving || isUpdating}
                  isSuccess={autoSave.isSuccess || isUpdateSuccess}
                  isError={autoSave.isError || isUpdateError}
                />

                {/* Show Reject and Approve buttons if not approved yet */}
                {!isApproved && (
                  <>
                    <button
                      onClick={handleRejectClick}
                      className="px-6 py-2 border border-red-600 text-red-600 rounded-md hover:bg-red-50 font-medium"
                      disabled={isRejecting}
                    >
                      {isRejecting ? 'Rejecting...' : 'Reject'}
                    </button>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span>
                          <button
                            onClick={handleApprove}
                            className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={isApproveBtnDisabled}
                          >
                            {isApproving ? 'Approving...' : 'Approve'}
                          </button>
                        </span>
                      </TooltipTrigger>
                      {isApproveBtnDisabled && (
                        <TooltipContent>
                          <p>Please wait for auto-save to complete</p>
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </>
                )}

                {/* Show Download Excel button if approved */}
                {isApproved && (
                  <button
                    onClick={handleDownload}
                    className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium flex items-center gap-2 disabled:opacity-50"
                    disabled={isExporting}
                  >
                    <Download size={18} />
                    {isExporting ? 'Downloading...' : 'Download Excel'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="container mx-auto px-6 py-8 max-w-7xl">
          {/* Validation Warnings */}
          {declaration.validation_warnings &&
            declaration.validation_warnings.length > 0 && (
              <div className="mb-6">
                <ValidationWarningsPanel
                  warnings={declaration.validation_warnings}
                />
              </div>
            )}

          {/* Corrections Log Panel */}
          <div className="mb-6">
            <CorrectionsLogPanel declarationId={id} />
          </div>

          {/* Declaration Form */}
          <DeclarationFormV2
            declarationId={id}
            initialData={declaration.draft_data}
            extractedData={declaration.extracted_data}
            confidenceScores={declaration.confidence_scores}
            onChange={handleFormChange}
            isSubmitting={autoSave.isSaving}
          />

          {/* Optional: Retry Save Link */}
          {autoSave.isError && (
            <div className="mt-6 text-center">
              <button
                onClick={autoSave.save}
                className="text-blue-600 hover:text-blue-700 underline text-sm"
              >
                Retry Save
              </button>
            </div>
          )}
        </div>

        {/* Reject Dialog */}
        <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reject Declaration</DialogTitle>
              <DialogDescription>
                Please provide a reason for rejecting this declaration (minimum
                10 characters).
              </DialogDescription>
            </DialogHeader>

            <textarea
              className="w-full border border-slate-300 rounded-md p-3 text-sm min-h-[120px] focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter rejection reason..."
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
            />

            <DialogFooter>
              <button
                onClick={() => setRejectDialogOpen(false)}
                className="px-4 py-2 border border-slate-300 rounded-md text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectConfirm}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                disabled={isRejecting || rejectionReason.trim().length < 10}
              >
                {isRejecting ? 'Rejecting...' : 'Confirm Reject'}
              </button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  )
}
