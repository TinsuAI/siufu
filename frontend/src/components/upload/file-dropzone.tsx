'use client';

import React, { useRef, useState } from 'react';
import { Check, Upload, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { FileType } from '@/types/upload';
import { validateFile, validateMimeType, getHumanReadableSize, getAcceptedFormatsString } from '@/lib/file-validators';
import { cn } from '@/lib/utils';

interface FileDropZoneProps {
  /**
   * Display label for the drop zone
   */
  label: string;

  /**
   * Type of file this drop zone accepts
   */
  fileType: FileType;

  /**
   * Accepted file formats (e.g., ['.pdf', '.jpg'])
   */
  acceptedFormats: string[];

  /**
   * Callback when a valid file is selected
   */
  onFileSelect: (file: File) => void;

  /**
   * Currently selected file (if any)
   */
  file: File | null;

  /**
   * Callback when file is removed
   */
  onRemove?: () => void;

  /**
   * Whether the drop zone is disabled
   */
  disabled?: boolean;
}

export function FileDropZone({
  label,
  fileType,
  acceptedFormats,
  onFileSelect,
  file,
  onRemove,
  disabled = false,
}: FileDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Handle file selection and validation
   */
  const handleFile = (selectedFile: File) => {
    // Clear previous error
    setError(null);

    // Validate file extension and size first
    const validationResult = validateFile(selectedFile, fileType);

    if (!validationResult.valid) {
      setError(validationResult.error || 'Invalid file');
      return;
    }

    // Validate MIME type (defense in depth - prevents renamed files)
    if (!validateMimeType(selectedFile, fileType)) {
      const extension = selectedFile.name.substring(selectedFile.name.lastIndexOf('.'));
      setError(`Invalid file type. File appears to be ${extension} but has incorrect MIME type (${selectedFile.type || 'unknown'}).`);
      return;
    }

    // File is valid, pass it to parent
    onFileSelect(selectedFile);
  };

  /**
   * Handle file input change (click to browse)
   */
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFile(selectedFile);
    }
    // Reset input value so the same file can be selected again
    e.target.value = '';
  };

  /**
   * Handle drag over event
   */
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  /**
   * Handle drag enter event
   */
  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  /**
   * Handle drag leave event
   */
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  /**
   * Handle drop event
   */
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      handleFile(droppedFile);
    }
  };

  /**
   * Handle click on drop zone (trigger file browser)
   */
  const handleClick = () => {
    if (!disabled && !file) {
      fileInputRef.current?.click();
    }
  };

  /**
   * Handle keyboard navigation (Enter or Space)
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if ((e.key === 'Enter' || e.key === ' ') && !disabled && !file) {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  /**
   * Handle remove button click
   */
  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    setError(null);
    onRemove?.();
  };

  // Determine border color based on state
  const getBorderColor = () => {
    if (error) return 'border-red-500';
    if (isDragOver) return 'border-blue-500';
    if (file) return 'border-green-500';
    return 'border-slate-300';
  };

  // Get accepted formats string for display
  const acceptedFormatsString = getAcceptedFormatsString(fileType);

  return (
    <div className="w-full">
      <Card
        className={cn(
          'relative border-2 border-dashed transition-colors cursor-pointer',
          getBorderColor(),
          disabled && 'opacity-50 cursor-not-allowed',
          !file && !disabled && 'hover:border-blue-400'
        )}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        tabIndex={disabled || file ? -1 : 0}
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
            aria-label={`File input for ${label}`}
          />

          {/* Label */}
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-slate-700">{label}</h3>
            {file && (
              <div className="flex items-center gap-2">
                <Check className="h-5 w-5 text-green-600" aria-label="File selected" />
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
          </div>

          {/* Content area */}
          <div className="flex flex-col items-center justify-center py-4">
            {file ? (
              // Display selected file info
              <div className="text-center">
                <p className="text-sm font-medium text-slate-700 break-all">{file.name}</p>
                <p className="text-xs text-slate-500 mt-1">{getHumanReadableSize(file.size)}</p>
              </div>
            ) : (
              // Display upload prompt
              <>
                <Upload className={cn('h-8 w-8 mb-2', isDragOver ? 'text-blue-500' : 'text-slate-400')} />
                <p className="text-sm text-slate-600 text-center mb-1">
                  {isDragOver ? 'Drop file here' : 'Drag and drop file here or click to browse'}
                </p>
                <p className="text-xs text-slate-500 text-center">{acceptedFormatsString}</p>
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Error message */}
      {error && (
        <div className="flex items-start gap-2 mt-2 p-2 bg-red-50 border border-red-200 rounded-md" role="alert">
          <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}
