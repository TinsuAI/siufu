'use client'

import React, { useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Check, Upload, X, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FileType } from '@/types/upload'
import {
  validateFile,
  validateMimeType,
  getHumanReadableSize,
  getAcceptedFormatsString,
} from '@/lib/file-validators'
import { cn } from '@/lib/utils'

interface FileDropZoneProps {
  /**
   * Display label for the drop zone
   */
  label: string

  /**
   * Type of file this drop zone accepts
   */
  fileType: FileType

  /**
   * Accepted file formats (e.g., ['.pdf', '.jpg'])
   */
  acceptedFormats: string[]

  /**
   * Callback when a valid file is selected (single-file mode)
   */
  onFileSelect?: (file: File) => void

  /**
   * Callback when valid files are selected (multi-file mode)
   */
  onFilesSelect?: (files: File[]) => void

  /**
   * Currently selected file (single-file mode)
   */
  file?: File | null

  /**
   * Currently selected files (multi-file mode)
   */
  files?: File[]

  /**
   * Callback when file is removed (single-file mode)
   */
  onRemove?: () => void

  /**
   * Callback when a specific file is removed (multi-file mode)
   */
  onRemoveFile?: (index: number) => void

  /**
   * Whether the drop zone is disabled
   */
  disabled?: boolean

  /**
   * Enable multi-file mode (default: false)
   */
  multiple?: boolean
}

export function FileDropZone({
  label,
  fileType,
  acceptedFormats,
  onFileSelect,
  onFilesSelect,
  file,
  files = [],
  onRemove,
  onRemoveFile,
  disabled = false,
  multiple = false,
}: FileDropZoneProps) {
  const t = useTranslations('upload.dropzone')
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Get current files list (for multi-file mode)
  const currentFiles = multiple ? files : []
  const hasFiles = multiple ? currentFiles.length > 0 : file !== null

  /**
   * Validate a single file
   */
  const validateSingleFile = (
    selectedFile: File
  ): { valid: boolean; error?: string } => {
    // Validate file extension and size first
    const validationResult = validateFile(selectedFile, fileType)

    if (!validationResult.valid) {
      return { valid: false, error: validationResult.error || 'Invalid file' }
    }

    // Validate MIME type (defense in depth - prevents renamed files)
    if (!validateMimeType(selectedFile, fileType)) {
      const extension = selectedFile.name.substring(
        selectedFile.name.lastIndexOf('.')
      )
      return {
        valid: false,
        error: `Invalid file type. File appears to be ${extension} but has incorrect MIME type (${selectedFile.type || 'unknown'}).`,
      }
    }

    return { valid: true }
  }

  /**
   * Handle file selection and validation (single-file mode)
   */
  const handleFile = (selectedFile: File) => {
    // Clear previous error
    setError(null)

    const validation = validateSingleFile(selectedFile)

    if (!validation.valid) {
      setError(validation.error || 'Invalid file')
      return
    }

    // File is valid, pass it to parent
    onFileSelect?.(selectedFile)
  }

  /**
   * Handle multiple files selection and validation (multi-file mode)
   */
  const handleFiles = (selectedFiles: FileList | File[]) => {
    // Clear previous error
    setError(null)

    const validFiles: File[] = []
    const errors: string[] = []

    // Convert FileList to Array
    const filesArray = Array.from(selectedFiles)

    // Validate each file
    for (const selectedFile of filesArray) {
      const validation = validateSingleFile(selectedFile)

      if (validation.valid) {
        validFiles.push(selectedFile)
      } else {
        errors.push(`${selectedFile.name}: ${validation.error}`)
      }
    }

    // Show errors if any
    if (errors.length > 0) {
      setError(errors.join('; '))
    }

    // Pass valid files to parent (append to existing files)
    if (validFiles.length > 0) {
      const newFiles = [...currentFiles, ...validFiles]
      onFilesSelect?.(newFiles)
    }
  }

  /**
   * Handle file input change (click to browse)
   */
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files
    if (selectedFiles && selectedFiles.length > 0) {
      if (multiple) {
        handleFiles(selectedFiles)
      } else {
        handleFile(selectedFiles[0])
      }
    }
    // Reset input value so the same file can be selected again
    e.target.value = ''
  }

  /**
   * Handle drag over event
   */
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragOver(true)
    }
  }

  /**
   * Handle drag enter event
   */
  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragOver(true)
    }
  }

  /**
   * Handle drag leave event
   */
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  /**
   * Handle drop event
   */
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    if (disabled) return

    const droppedFiles = e.dataTransfer.files
    if (droppedFiles && droppedFiles.length > 0) {
      if (multiple) {
        handleFiles(droppedFiles)
      } else {
        handleFile(droppedFiles[0])
      }
    }
  }

  /**
   * Handle click on drop zone (trigger file browser)
   */
  const handleClick = () => {
    if (!disabled) {
      // In multi-file mode, always allow adding more files
      // In single-file mode, only allow if no file is selected
      if (multiple || !file) {
        fileInputRef.current?.click()
      }
    }
  }

  /**
   * Handle keyboard navigation (Enter or Space)
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
      if (multiple || !file) {
        e.preventDefault()
        fileInputRef.current?.click()
      }
    }
  }

  /**
   * Handle remove button click (single-file mode)
   */
  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation()
    setError(null)
    onRemove?.()
  }

  /**
   * Handle remove individual file button click (multi-file mode)
   */
  const handleRemoveFileAtIndex = (index: number) => (e: React.MouseEvent) => {
    e.stopPropagation()
    setError(null)
    onRemoveFile?.(index)
  }

  // Determine border color based on state
  const getBorderColor = () => {
    if (error) return 'border-red-500'
    if (isDragOver) return 'border-blue-500'
    if (hasFiles) return 'border-green-500'
    return 'border-slate-300'
  }

  // Get accepted formats string for display
  const acceptedFormatsString = getAcceptedFormatsString(fileType)

  return (
    <div className="w-full">
      <Card
        className={cn(
          'relative border-2 border-dashed transition-colors cursor-pointer',
          getBorderColor(),
          disabled && 'opacity-50 cursor-not-allowed',
          !hasFiles && !disabled && 'hover:border-blue-400'
        )}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        role="button"
        aria-label={`Upload ${label}`}
        aria-disabled={disabled}
      >
        <div className="p-6">
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept={acceptedFormats.join(',')}
            onChange={handleFileInputChange}
            className="hidden"
            disabled={disabled}
            multiple={multiple}
            aria-label={`File input for ${label}`}
          />

          {/* Label */}
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-slate-700">{label}</h3>
            {!multiple && file && (
              <div className="flex items-center gap-2">
                <Check
                  className="h-5 w-5 text-green-600"
                  aria-label="File selected"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRemove}
                  disabled={disabled}
                  aria-label={`Remove ${label}`}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
            {multiple && currentFiles.length > 0 && (
              <div className="flex items-center gap-2">
                <Check
                  className="h-5 w-5 text-green-600"
                  aria-label="Files selected"
                />
                <span className="text-sm font-medium text-green-700 bg-green-100 px-2 py-1 rounded">
                  {currentFiles.length}{' '}
                  {currentFiles.length === 1 ? t('file') : t('files')}
                </span>
              </div>
            )}
          </div>

          {/* Content area */}
          <div className="flex flex-col items-center justify-center py-4">
            {!multiple && file ? (
              // Display selected file info (single-file mode)
              <div className="text-center">
                <p className="text-sm font-medium text-slate-700 break-all">
                  {file.name}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {getHumanReadableSize(file.size)}
                </p>
              </div>
            ) : multiple && currentFiles.length > 0 ? (
              // Display list of files (multi-file mode)
              <div className="w-full space-y-2">
                {currentFiles.map((fileItem, index) => (
                  <div
                    key={`${fileItem.name}-${index}`}
                    className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-200"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-700 truncate">
                        {fileItem.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {getHumanReadableSize(fileItem.size)}
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={handleRemoveFileAtIndex(index)}
                      disabled={disabled}
                      aria-label={`Remove ${fileItem.name}`}
                      className="h-8 w-8 p-0 ml-2 flex-shrink-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                {/* Add more files prompt */}
                <div className="flex items-center justify-center py-2 border-t border-slate-200 mt-2">
                  <Upload className="h-6 w-6 mr-2 text-slate-400" />
                  <p className="text-sm text-slate-600">
                    {isDragOver ? t('dropMoreFiles') : t('clickOrDragMore')}
                  </p>
                </div>
              </div>
            ) : (
              // Display upload prompt (no files selected)
              <>
                <Upload
                  className={cn(
                    'h-8 w-8 mb-2',
                    isDragOver ? 'text-blue-500' : 'text-slate-400'
                  )}
                />
                <p className="text-sm text-slate-600 text-center mb-1">
                  {isDragOver
                    ? multiple
                      ? t('dropMultiple')
                      : t('dropSingle')
                    : multiple
                      ? t('dragAndDropMultiple')
                      : t('dragAndDropSingle')}
                </p>
                <p className="text-xs text-slate-500 text-center">
                  {acceptedFormatsString}
                </p>
                {multiple && (
                  <p className="text-xs text-slate-400 text-center mt-1">
                    {t('multipleSupported')}
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Error message */}
      {error && (
        <div
          className="flex items-start gap-2 mt-2 p-2 bg-red-50 border border-red-200 rounded-md"
          role="alert"
        >
          <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  )
}
