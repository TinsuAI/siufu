/**
 * Declaration Review Page
 *
 * Full review interface with editable form, confidence indicators, auto-save,
 * and approve/reject/export functionality
 */

'use client'

import React, { useState, useEffect } from 'react'
import { use } from 'react'
import { useRouter } from '@/navigation'
import { useTranslations } from 'next-intl'
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
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Download } from 'lucide-react'

interface DeclarationReviewPageProps {
  params: Promise<{ id: string }>
}

export default function DeclarationReviewPage({
  params,
}: DeclarationReviewPageProps) {
  const { id } = use(params)
  const router = useRouter()
  const t = useTranslations('declarations.review')
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
        title: t('toasts.invalidReason.title'),
        description: t('toasts.invalidReason.description'),
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
        title: t('toasts.approveSuccess.title'),
        description: t('toasts.approveSuccess.description'),
        variant: 'success',
      })
    }
  }, [isApproveSuccess, toast, t])

  // Show success toast on rejection and redirect
  useEffect(() => {
    if (isRejectSuccess) {
      toast({
        title: t('toasts.rejectSuccess.title'),
        description: t('toasts.rejectSuccess.description'),
        variant: 'success',
      })
      setRejectDialogOpen(false)
      // Redirect to declarations list after 1 second
      setTimeout(() => {
        router.push('/declarations')
      }, 1000)
    }
  }, [isRejectSuccess, toast, router, t])

  // Show success message on export
  useEffect(() => {
    if (isExportSuccess) {
      toast({
        title: t('toasts.exportSuccess.title'),
        description: t('toasts.exportSuccess.description'),
        variant: 'success',
      })
    }
  }, [isExportSuccess, toast, t])

  // Show error toasts
  useEffect(() => {
    if (isApproveError) {
      toast({
        title: t('toasts.approveError.title'),
        description: t('toasts.approveError.description'),
        variant: 'error',
      })
    }
  }, [isApproveError, toast, t])

  useEffect(() => {
    if (isRejectError) {
      toast({
        title: t('toasts.rejectError.title'),
        description: t('toasts.rejectError.description'),
        variant: 'error',
      })
    }
  }, [isRejectError, toast, t])

  useEffect(() => {
    if (isExportError) {
      toast({
        title: t('toasts.exportError.title'),
        description: t('toasts.exportError.description'),
        variant: 'error',
      })
    }
  }, [isExportError, toast, t])

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
            <p className="text-slate-600">{t('loadingDeclaration')}</p>
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
            {t('errorLoading')}
          </h2>
          <p className="text-red-600">
            {error?.message || t('unexpectedError')}
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
            {t('notFound')}
          </h2>
          <p className="text-yellow-600">{t('notFoundMessage')}</p>
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
                  {t('title')}
                </h1>
                <p className="text-sm text-slate-600">
                  {t('idLabel')}: {declaration.id} • {t('statusLabel')}:{' '}
                  {declaration.status}
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
                      {isRejecting
                        ? t('buttons.rejecting')
                        : t('buttons.reject')}
                    </button>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span>
                          <button
                            onClick={handleApprove}
                            className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={isApproveBtnDisabled}
                          >
                            {isApproving
                              ? t('buttons.approving')
                              : t('buttons.approve')}
                          </button>
                        </span>
                      </TooltipTrigger>
                      {isApproveBtnDisabled && (
                        <TooltipContent>
                          <p>{t('tooltips.waitForAutoSave')}</p>
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
                    {isExporting
                      ? t('buttons.downloading')
                      : t('buttons.downloadExcel')}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="container mx-auto px-6 py-8 max-w-7xl">
          <Tabs defaultValue="declaration" className="w-full">
            <TabsList className="mb-6">
              <TabsTrigger value="declaration">
                {t('tabs.declarationForm')}
              </TabsTrigger>
              <TabsTrigger value="validation" className="relative">
                {t('tabs.validation')}
                {declaration.validation_warnings &&
                  declaration.validation_warnings.length > 0 && (
                    <Badge
                      variant="destructive"
                      className="ml-2 h-5 min-w-5 px-1.5"
                    >
                      {declaration.validation_warnings.length}
                    </Badge>
                  )}
              </TabsTrigger>
              <TabsTrigger value="corrections">
                {t('tabs.corrections')}
              </TabsTrigger>
            </TabsList>

            {/* Declaration Form Tab */}
            <TabsContent value="declaration" className="space-y-6">
              {/* Declaration Form */}
              <DeclarationFormV2
                declarationId={id}
                initialData={declaration.draft_data}
                extractedData={declaration.extracted_data}
                confidenceScores={declaration.confidence_scores}
                sourceMetadata={declaration.source_metadata}
                importerId={declaration.importer_id}
                exporterId={declaration.exporter_id}
                importerDeclarationCount={
                  declaration.importer_summary?.declaration_count
                }
                exporterDeclarationCount={
                  declaration.exporter_summary?.declaration_count
                }
                importerSummary={declaration.importer_summary}
                exporterSummary={declaration.exporter_summary}
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
                    {t('buttons.retrySave')}
                  </button>
                </div>
              )}
            </TabsContent>

            {/* Cross-Document Validation Tab */}
            <TabsContent value="validation">
              <div className="space-y-4">
                {declaration.validation_warnings &&
                declaration.validation_warnings.length > 0 ? (
                  <ValidationWarningsPanel
                    warnings={declaration.validation_warnings}
                    declarationId={id}
                    defaultOpen={true}
                  />
                ) : (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
                    <div className="flex justify-center mb-4">
                      <div className="rounded-full bg-green-100 p-3">
                        <svg
                          className="h-8 w-8 text-green-600"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      </div>
                    </div>
                    <h3 className="text-lg font-semibold text-green-900 mb-2">
                      {t('validationMessages.noIssues')}
                    </h3>
                    <p className="text-green-700 text-sm max-w-md mx-auto">
                      {t('validationMessages.noIssuesDescription')}
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Corrections Log Tab */}
            <TabsContent value="corrections">
              <CorrectionsLogPanel declarationId={id} />
            </TabsContent>
          </Tabs>
        </div>

        {/* Reject Dialog */}
        <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('rejectDialog.title')}</DialogTitle>
              <DialogDescription>
                {t('rejectDialog.description')}
              </DialogDescription>
            </DialogHeader>

            <textarea
              className="w-full border border-slate-300 rounded-md p-3 text-sm min-h-[120px] focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t('rejectDialog.placeholder')}
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
            />

            <DialogFooter>
              <button
                onClick={() => setRejectDialogOpen(false)}
                className="px-4 py-2 border border-slate-300 rounded-md text-slate-700 hover:bg-slate-50"
              >
                {t('rejectDialog.cancel')}
              </button>
              <button
                onClick={handleRejectConfirm}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                disabled={isRejecting || rejectionReason.trim().length < 10}
              >
                {isRejecting
                  ? t('buttons.rejecting')
                  : t('rejectDialog.confirm')}
              </button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  )
}
