/**
 * Field Flag Button Component (Story 3.6 Expansion)
 *
 * Inline button to flag field corrections with category and notes
 */

'use client'

import React, { useState } from 'react'
import { Flag, Upload, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createCorrection, getCorrections } from '@/lib/api'
import type { CorrectionCategory, CorrectionCreate } from '@/types/declaration'
import { FieldLabel } from './field-label'
import { useSourceMetadata } from './source-metadata-context'

interface FieldFlagButtonProps {
  declarationId: string
  fieldName: string
  originalValue: string | number | null | undefined
  correctedValue: string | number | null | undefined
  label?: string
}

const CORRECTION_CATEGORIES: CorrectionCategory[] = [
  'AI Extraction Error',
  'Wrong HS Code',
  'Calculation Error',
  'Missing Data',
  'Format Issue',
  'Other',
]

export function FieldFlagButton({
  declarationId,
  fieldName,
  originalValue,
  correctedValue,
  label,
}: FieldFlagButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [category, setCategory] = useState<CorrectionCategory | ''>('')
  const [expectedValue, setExpectedValue] = useState('')
  const [notes, setNotes] = useState('')
  const [screenshots, setScreenshots] = useState<File[]>([])
  const sourceMetadata = useSourceMetadata()
  const formattedLabel =
    label ||
    fieldName
      .replace(/\[(\d+)\]/g, ' $1 ')
      .replace(/[._]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .replace(/(^|\s)\w/g, (match) => match.toUpperCase())

  const queryClient = useQueryClient()

  // Fetch existing corrections for this declaration
  const { data: correctionsData } = useQuery({
    queryKey: ['declarations', declarationId, 'corrections'],
    queryFn: () => getCorrections(declarationId),
    enabled: !!declarationId,
  })

  // Find existing correction for this specific field
  const existingCorrection = correctionsData?.corrections?.find(
    (c) => c.field_name === fieldName
  )

  // Pre-populate form when opening if there's an existing correction
  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (open && existingCorrection) {
      setCategory(existingCorrection.correction_category)
      setExpectedValue(existingCorrection.expected_value)
      setNotes(existingCorrection.notes)
      // Note: screenshots are URLs, not files, so we don't pre-populate them
    } else if (!open) {
      // Reset form when closing
      setCategory('')
      setExpectedValue('')
      setNotes('')
      setScreenshots([])
    }
  }

  const createCorrectionMutation = useMutation({
    mutationFn: ({
      declarationId: declId,
      correctionData,
    }: {
      declarationId: string
      correctionData: CorrectionCreate
    }) => createCorrection(declId, correctionData),
    onSuccess: () => {
      // Invalidate corrections query to refetch
      queryClient.invalidateQueries({
        queryKey: ['declarations', declarationId, 'corrections'],
      })
      // Close popover and reset form
      setIsOpen(false)
      setCategory('')
      setExpectedValue('')
      setNotes('')
      setScreenshots([])
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    // Limit to 3 screenshots
    setScreenshots((prev) => [...prev, ...files].slice(0, 3))
  }

  const removeScreenshot = (index: number) => {
    setScreenshots((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSave = async () => {
    if (!category || !expectedValue || !notes) return

    // Convert corrected value to string
    const correctedValueStr =
      correctedValue === null || correctedValue === undefined
        ? ''
        : String(correctedValue)

    // Convert original value to string or null
    const originalValueStr =
      originalValue === null || originalValue === undefined
        ? null
        : String(originalValue)

    // TODO: Upload screenshots to backend first, then include URLs in correction data
    // For now, we'll just save the correction without screenshots
    await createCorrectionMutation.mutateAsync({
      declarationId,
      correctionData: {
        field_name: fieldName,
        original_value: originalValueStr,
        corrected_value: correctedValueStr,
        correction_category: category,
        expected_value: expectedValue,
        notes: notes,
        // screenshots: [], // Will be added after backend support
      },
    })
  }

  const isFlagged = !!existingCorrection

  return (
    <div className="ml-2 flex items-center gap-1">
      {sourceMetadata && (
        <FieldLabel
          label={formattedLabel || fieldName}
          fieldPath={fieldName}
          sourceMetadata={sourceMetadata}
          variant="icon-only"
          hideWhenNoSource
        />
      )}
      <Popover open={isOpen} onOpenChange={handleOpenChange}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className={`h-6 w-6 p-0 ${
              isFlagged
                ? 'bg-orange-100 hover:bg-orange-200'
                : 'hover:bg-orange-100'
            }`}
            type="button"
            title={isFlagged ? 'Edit flag' : 'Flag this correction'}
          >
            <Flag
              className={`h-3.5 w-3.5 ${
                isFlagged
                  ? 'text-orange-600 fill-orange-600'
                  : 'text-orange-600'
              }`}
            />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-96 max-h-[600px] overflow-y-auto">
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">
                {isFlagged ? 'Edit Flag' : 'Flag Correction'}
              </h4>
              <p className="text-sm text-muted-foreground mb-4">
                {isFlagged
                  ? 'Update the correction details for this field.'
                  : 'Help us improve AI extraction by providing the correct value and context.'}
              </p>
              {isFlagged && (
                <p className="text-xs text-blue-600 bg-blue-50 p-2 rounded mb-2">
                  This field already has a flag. Updating will replace the
                  existing flag.
                </p>
              )}
            </div>

            {/* Correction Category */}
            <div className="space-y-2">
              <Label
                htmlFor="correction-category"
                className="text-sm font-medium"
              >
                Correction Category *
              </Label>
              <Select
                value={category}
                onValueChange={(value) =>
                  setCategory(value as CorrectionCategory)
                }
              >
                <SelectTrigger id="correction-category">
                  <SelectValue placeholder="Select category..." />
                </SelectTrigger>
                <SelectContent>
                  {CORRECTION_CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Expected Value */}
            <div className="space-y-2">
              <Label htmlFor="expected-value" className="text-sm font-medium">
                Expected Value *
              </Label>
              <Input
                id="expected-value"
                value={expectedValue}
                onChange={(e) => setExpectedValue(e.target.value)}
                placeholder="What should the correct value be?"
                maxLength={500}
              />
              <p className="text-xs text-muted-foreground">
                The value that should have been extracted from the document
              </p>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <Label htmlFor="correction-notes" className="text-sm font-medium">
                Notes *
              </Label>
              <Textarea
                id="correction-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value.slice(0, 500))}
                placeholder="Explain why this is wrong and where the correct value is located..."
                className="h-24 resize-none"
                maxLength={500}
              />
              <p className="text-xs text-muted-foreground text-right">
                {notes.length}/500
              </p>
            </div>

            {/* Screenshot Upload */}
            <div className="space-y-2">
              <Label htmlFor="screenshots" className="text-sm font-medium">
                Screenshots (optional, max 3)
              </Label>
              <div className="space-y-2">
                <Input
                  id="screenshots"
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleFileChange}
                  disabled={screenshots.length >= 3}
                  className="cursor-pointer"
                />
                <p className="text-xs text-muted-foreground">
                  Upload screenshots showing where the correct data appears in
                  the document
                </p>

                {/* Preview uploaded screenshots */}
                {screenshots.length > 0 && (
                  <div className="space-y-1">
                    {screenshots.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-slate-50 p-2 rounded text-sm"
                      >
                        <span className="flex items-center gap-2 truncate">
                          <Upload className="h-4 w-4 text-slate-500" />
                          <span className="truncate">{file.name}</span>
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeScreenshot(index)}
                          className="h-6 w-6 p-0"
                          type="button"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {createCorrectionMutation.isError && (
              <p className="text-sm text-red-600">
                Failed to save correction. Please try again.
              </p>
            )}

            <div className="flex gap-2">
              <Button
                onClick={handleSave}
                disabled={
                  !category ||
                  !expectedValue ||
                  !notes ||
                  createCorrectionMutation.isPending
                }
                className="flex-1"
              >
                {createCorrectionMutation.isPending
                  ? 'Saving...'
                  : isFlagged
                    ? 'Update Flag'
                    : 'Save Flag'}
              </Button>
              <Button
                variant="outline"
                onClick={() => setIsOpen(false)}
                className="flex-1"
                type="button"
              >
                Cancel
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}
