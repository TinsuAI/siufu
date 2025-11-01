/**
 * Unit tests for ProcessingStepper component
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProcessingStepper } from '@/components/declarations/processing-stepper'
import { DeclarationStatus } from '@/types/declaration'

describe('ProcessingStepper', () => {
  it('should render all processing stages', () => {
    render(
      <ProcessingStepper status={DeclarationStatus.PROCESSING} progress={0.5} />
    )

    // Check that all stage labels are present (using getAllByText since labels appear in both badge and message)
    expect(screen.getAllByText('Uploading').length).toBeGreaterThan(0)
    expect(screen.getAllByText('OCR Processing').length).toBeGreaterThan(0)
    expect(screen.getAllByText('AI Extraction').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Validation').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Generating Excel').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Ready for Review').length).toBeGreaterThan(0)
  })

  it('should highlight active stage for OCR Processing', () => {
    render(
      <ProcessingStepper status={DeclarationStatus.PROCESSING} progress={0.2} />
    )

    // OCR Processing should be active (progress < 0.3)
    const ocrBadges = screen.getAllByText('OCR Processing')
    expect(ocrBadges[0]).toHaveClass('bg-blue-500')

    // Processing Progress should be displayed
    expect(screen.getByText('Processing Progress')).toBeInTheDocument()
    expect(screen.getByText('20%')).toBeInTheDocument()
  })

  it('should highlight active stage for AI Extraction', () => {
    render(
      <ProcessingStepper status={DeclarationStatus.PROCESSING} progress={0.5} />
    )

    // AI Extraction should be active (progress 0.3-0.7)
    const aiBadges = screen.getAllByText('AI Extraction')
    expect(aiBadges[0]).toHaveClass('bg-blue-500')

    // Progress percentage should be 50%
    expect(screen.getByText('50%')).toBeInTheDocument()
  })

  it('should highlight active stage for Validation', () => {
    render(
      <ProcessingStepper status={DeclarationStatus.VALIDATING} progress={0.8} />
    )

    // Validation should be active
    const validationBadges = screen.getAllByText('Validation')
    expect(validationBadges[0]).toHaveClass('bg-blue-500')

    // Progress percentage should be 80%
    expect(screen.getByText('80%')).toBeInTheDocument()
  })

  it('should show completed stages with green styling', () => {
    render(
      <ProcessingStepper status={DeclarationStatus.VALIDATING} progress={0.8} />
    )

    // Earlier stages should be completed (green)
    const uploadingBadges = screen.getAllByText('Uploading')
    const ocrBadges = screen.getAllByText('OCR Processing')
    const aiBadges = screen.getAllByText('AI Extraction')

    // These should have secondary variant (completed)
    expect(uploadingBadges[0]).toHaveClass('bg-green-500')
    expect(ocrBadges[0]).toHaveClass('bg-green-500')
    expect(aiBadges[0]).toHaveClass('bg-green-500')
  })

  it('should update progress bar with processing_progress value', () => {
    const { rerender } = render(
      <ProcessingStepper status={DeclarationStatus.PROCESSING} progress={0.3} />
    )

    // Initial progress: 30%
    expect(screen.getByText('30%')).toBeInTheDocument()

    // Update to 60%
    rerender(
      <ProcessingStepper status={DeclarationStatus.PROCESSING} progress={0.6} />
    )

    expect(screen.getByText('60%')).toBeInTheDocument()

    // Update to 90%
    rerender(
      <ProcessingStepper status={DeclarationStatus.VALIDATING} progress={0.9} />
    )

    expect(screen.getByText('90%')).toBeInTheDocument()
  })

  it('should display READY_FOR_REVIEW stage correctly', () => {
    render(
      <ProcessingStepper
        status={DeclarationStatus.READY_FOR_REVIEW}
        progress={1.0}
      />
    )

    // Ready for Review badge should be active
    const readyBadges = screen.getAllByText('Ready for Review')
    expect(readyBadges[0]).toHaveClass('bg-blue-500')

    // Progress should be 100%
    expect(screen.getByText('100%')).toBeInTheDocument()

    // Current stage message should show Ready for Review
    expect(screen.getByText(/Currently:/)).toBeInTheDocument()
  })

  it('should display failed status correctly', () => {
    render(
      <ProcessingStepper status={DeclarationStatus.FAILED} progress={0.4} />
    )

    // Should show "Processing Failed" message
    expect(screen.getByText('Processing Failed')).toBeInTheDocument()

    // Progress should still be displayed
    expect(screen.getByText('40%')).toBeInTheDocument()
  })

  it('should map backend status to correct frontend stage', () => {
    // Test UPLOADED -> UPLOADING
    const { rerender } = render(
      <ProcessingStepper status={DeclarationStatus.UPLOADED} progress={0.0} />
    )
    const uploadingBadges = screen.getAllByText('Uploading')
    expect(uploadingBadges[0]).toHaveClass('bg-blue-500')

    // Test PROCESSING with low progress -> OCR_PROCESSING
    rerender(
      <ProcessingStepper status={DeclarationStatus.PROCESSING} progress={0.1} />
    )
    const ocrBadges = screen.getAllByText('OCR Processing')
    expect(ocrBadges[0]).toHaveClass('bg-blue-500')

    // Test PROCESSING with mid progress -> AI_EXTRACTION
    rerender(
      <ProcessingStepper status={DeclarationStatus.PROCESSING} progress={0.5} />
    )
    const aiBadges = screen.getAllByText('AI Extraction')
    expect(aiBadges[0]).toHaveClass('bg-blue-500')

    // Test PROCESSING with high progress -> VALIDATING
    rerender(
      <ProcessingStepper status={DeclarationStatus.PROCESSING} progress={0.8} />
    )
    const validationBadges = screen.getAllByText('Validation')
    expect(validationBadges[0]).toHaveClass('bg-blue-500')

    // Test VALIDATING with very high progress -> GENERATING_EXCEL
    rerender(
      <ProcessingStepper
        status={DeclarationStatus.VALIDATING}
        progress={0.95}
      />
    )
    const excelBadges = screen.getAllByText('Generating Excel')
    expect(excelBadges[0]).toHaveClass('bg-blue-500')
  })

  it('should apply custom className when provided', () => {
    const { container } = render(
      <ProcessingStepper
        status={DeclarationStatus.PROCESSING}
        progress={0.5}
        className="custom-class"
      />
    )

    const stepperDiv = container.firstChild as HTMLElement
    expect(stepperDiv).toHaveClass('custom-class')
  })
})
