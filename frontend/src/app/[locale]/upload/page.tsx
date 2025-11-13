'use client'

import React, { useEffect } from 'react'
import { useRouter } from '@/navigation'
import { Loader2, AlertCircle, FileUp } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { FileDropZone } from '@/components/upload/file-dropzone'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useUploadStore } from '@/stores/upload-store'
import { useUploadDeclaration } from '@/hooks/use-upload'
import { useAuth } from '@/hooks/use-auth'
import {
  FileType,
  ACCEPTED_FORMATS,
  FILE_TYPE_LABELS,
  FILE_NAME_PATTERNS,
} from '@/types/upload'

/**
 * Configuration for each file drop zone
 * Updated in Story 3.3.1: Removed GOODLIST and TARIFF zones
 */
const getFileZones = (
  t: (key: string) => string
): Array<{
  fileType: FileType
  label: string
  description: string
  multiple?: boolean
}> => [
  {
    fileType: 'AN',
    label: `${FILE_TYPE_LABELS.AN} (${FILE_NAME_PATTERNS.AN})`,
    description: t('descriptions.AN'),
  },
  {
    fileType: 'BOL',
    label: `${FILE_TYPE_LABELS.BOL} (${FILE_NAME_PATTERNS.BOL})`,
    description: t('descriptions.BOL'),
  },
  {
    fileType: 'CO',
    label: t('documentTypes.CO'),
    description: t('descriptions.CO'),
    multiple: true,
  },
  {
    fileType: 'INVOICE',
    label: `${FILE_TYPE_LABELS.INVOICE} (${FILE_NAME_PATTERNS.INVOICE})`,
    description: t('descriptions.INVOICE'),
  },
]

export default function UploadPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()
  const t = useTranslations('upload')

  // Upload store state
  const {
    files,
    isUploading,
    setFile,
    removeFile,
    reset,
    allFilesUploaded,
    uploadedCount,
  } = useUploadStore()

  // Upload mutation
  const uploadMutation = useUploadDeclaration()

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, router])

  // Reset upload store when component unmounts or user navigates away
  useEffect(() => {
    return () => {
      reset()
    }
  }, [reset])

  /**
   * Handle file selection for a specific drop zone (single-file mode)
   */
  const handleFileSelect = (fileType: FileType, file: File) => {
    setFile(fileType, file)
  }

  /**
   * Handle files selection for C/O drop zone (multi-file mode)
   */
  const handleFilesSelect = (fileType: FileType, selectedFiles: File[]) => {
    // For multi-file mode (C/O), update the entire files array
    if (fileType === 'CO') {
      // The store should handle this properly
      // For now, we'll use a different method in the store
      useUploadStore.getState().setCOFiles(selectedFiles)
    }
  }

  /**
   * Handle file removal for a specific drop zone (single-file mode)
   */
  const handleFileRemove = (fileType: FileType) => {
    removeFile(fileType)
  }

  /**
   * Handle individual C/O file removal (multi-file mode)
   */
  const handleCOFileRemove = (index: number) => {
    useUploadStore.getState().removeCOFile(index)
  }

  /**
   * Handle process declaration button click
   */
  const handleProcessDeclaration = () => {
    if (allFilesUploaded()) {
      uploadMutation.mutate(files)
    }
  }

  /**
   * Handle retry after error
   */
  const handleRetry = () => {
    uploadMutation.reset()
    if (allFilesUploaded()) {
      uploadMutation.mutate(files)
    }
  }

  // Show loading if authentication check is in progress
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    )
  }

  const uploadCount = uploadedCount()
  const isProcessButtonDisabled = !allFilesUploaded() || isUploading
  const FILE_ZONES = getFileZones(t)

  return (
    <div className="container mx-auto px-6 py-8 max-w-7xl">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800 mb-2">{t('title')}</h1>
        <p className="text-slate-600">{t('subtitle')}</p>
      </div>

      {/* Upload Progress */}
      <Card className="mb-6 p-4 bg-blue-50 border-blue-200">
        <div className="flex items-center gap-3">
          <FileUp className="h-5 w-5 text-blue-600" />
          <div>
            <p className="text-sm font-medium text-blue-900">
              {t('progress.label')}:{' '}
              {t('progress.count', { count: uploadCount })}
            </p>
            {uploadCount === 4 && (
              <p className="text-xs text-blue-700 mt-0.5">
                {t('progress.complete')}
              </p>
            )}
          </div>
        </div>
      </Card>

      {/* Error Display */}
      {uploadMutation.isError && (
        <Card
          className="mb-6 p-4 bg-red-50 border-red-200"
          role="alert"
          aria-live="assertive"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-900 mb-1">
                {t('messages.uploadFailed')}
              </h3>
              <p className="text-sm text-red-700">
                {uploadMutation.error?.message || t('messages.uploadError')}
              </p>
              <Button
                onClick={handleRetry}
                variant="outline"
                size="sm"
                className="mt-3 border-red-300 text-red-700 hover:bg-red-100"
              >
                {t('buttons.retry')}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* File Drop Zones Grid - Updated in Story 3.3.1: 2x2 grid for 4 file types */}
      <div
        className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8"
        role="group"
        aria-label="File upload zones"
      >
        {FILE_ZONES.map(({ fileType, label, description, multiple }) => {
          const fieldName = {
            AN: 'arrival_notice',
            BOL: 'bill_of_lading',
            CO: 'certificate_of_origin',
            INVOICE: 'invoice',
          }[fileType] as keyof typeof files

          // For C/O (multi-file mode), use different props
          if (multiple && fileType === 'CO') {
            return (
              <div key={fileType} title={description}>
                <FileDropZone
                  label={label}
                  fileType={fileType}
                  acceptedFormats={ACCEPTED_FORMATS[fileType]}
                  multiple={true}
                  files={files[fieldName] as File[]}
                  onFilesSelect={(selectedFiles) =>
                    handleFilesSelect(fileType, selectedFiles)
                  }
                  onRemoveFile={handleCOFileRemove}
                  disabled={isUploading}
                />
              </div>
            )
          }

          // For other file types (single-file mode)
          return (
            <div key={fileType} title={description}>
              <FileDropZone
                label={label}
                fileType={fileType}
                acceptedFormats={ACCEPTED_FORMATS[fileType]}
                file={files[fieldName] as File | null}
                onFileSelect={(file) => handleFileSelect(fileType, file)}
                onRemove={() => handleFileRemove(fileType)}
                disabled={isUploading}
              />
            </div>
          )
        })}
      </div>

      {/* Process Declaration Button */}
      <div className="flex flex-col items-center gap-4">
        <Button
          onClick={handleProcessDeclaration}
          disabled={isProcessButtonDisabled}
          size="lg"
          className="w-full md:w-auto px-12"
          aria-label="Process declaration with uploaded files"
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              {t('buttons.uploading')}
            </>
          ) : (
            t('buttons.process')
          )}
        </Button>

        {!allFilesUploaded() && !isUploading && (
          <p className="text-sm text-slate-500" aria-live="polite">
            {t('messages.uploadRequired')}
          </p>
        )}
      </div>

      {/* Help Text */}
      <Card className="mt-8 p-6 bg-slate-50 border-slate-200">
        <h3 className="text-sm font-medium text-slate-800 mb-3">
          {t('helpAndTips.title')}
        </h3>
        <ul className="text-sm text-slate-600 space-y-2">
          <li className="flex items-start gap-2">
            <span className="text-slate-400">•</span>
            <span>{t('helpAndTips.dragDrop')}</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-slate-400">•</span>
            <span>{t('helpAndTips.multipleFiles')}</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-slate-400">•</span>
            <span>{t('helpAndTips.validation')}</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-slate-400">•</span>
            <span>{t('helpAndTips.maxSizes')}</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-slate-400">•</span>
            <span>{t('helpAndTips.requiredDocs')}</span>
          </li>
        </ul>
      </Card>
    </div>
  )
}
