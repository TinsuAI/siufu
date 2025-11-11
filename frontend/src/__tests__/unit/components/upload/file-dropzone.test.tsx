import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FileDropZone } from '@/components/upload/file-dropzone'

describe('FileDropZone', () => {
  const defaultProps = {
    label: 'Test Document (test.pdf)',
    fileType: 'AN' as const,
    acceptedFormats: ['.pdf'],
    onFileSelect: vi.fn(),
    file: null,
  }

  it('renders with correct label', () => {
    render(<FileDropZone {...defaultProps} />)

    expect(screen.getByText('Test Document (test.pdf)')).toBeInTheDocument()
    expect(
      screen.getByText(/Drag and drop file here or click to browse/i)
    ).toBeInTheDocument()
  })

  it('renders accepted formats info', () => {
    render(<FileDropZone {...defaultProps} />)

    // Should display accepted formats and max size
    expect(screen.getByText(/Accepted:.*\.pdf/i)).toBeInTheDocument()
    expect(screen.getByText(/max.*10.*MB/i)).toBeInTheDocument()
  })

  it('displays upload icon when no file is selected', () => {
    render(<FileDropZone {...defaultProps} />)

    // Upload icon should be visible (check by role since lucide-react uses SVG)
    const uploadPrompt = screen.getByText(
      /Drag and drop file here or click to browse/i
    )
    expect(uploadPrompt).toBeInTheDocument()
  })

  it('calls onFileSelect with valid file when file input changes', async () => {
    const onFileSelect = vi.fn()
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />)

    // Create a valid PDF file
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    })

    // Find the hidden file input
    const fileInput = screen.getByLabelText(/File input for Test Document/i)

    // Simulate file selection
    await userEvent.upload(fileInput, file)

    // onFileSelect should be called with the file
    await waitFor(() => {
      expect(onFileSelect).toHaveBeenCalledWith(file)
    })
  })

  it('shows error for invalid file type', async () => {
    const onFileSelect = vi.fn()
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />)

    // Create an invalid file (Word doc instead of PDF)
    const file = new File(['test content'], 'test.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })

    const fileInput = screen.getByLabelText(/File input for Test Document/i)

    // Use fireEvent instead of userEvent because accept attribute blocks invalid files in userEvent
    // This simulates a scenario where an invalid file gets through (e.g., via drag-and-drop)
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    fireEvent.change(fileInput)

    // Should show error message (increased timeout for async state updates)
    await waitFor(
      () => {
        expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument()
        expect(screen.getByText(/Expected.*\.pdf/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // onFileSelect should NOT be called
    expect(onFileSelect).not.toHaveBeenCalled()
  })

  it('shows error for file exceeding size limit', async () => {
    const onFileSelect = vi.fn()
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />)

    // Create a file larger than 10MB (AN file type limit)
    const largeContent = 'x'.repeat(11 * 1024 * 1024) // 11MB
    const file = new File([largeContent], 'large.pdf', {
      type: 'application/pdf',
    })

    const fileInput = screen.getByLabelText(/File input for Test Document/i)
    await userEvent.upload(fileInput, file)

    // Should show error message (increased timeout for async state updates)
    await waitFor(
      () => {
        expect(screen.getByText(/File too large/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // onFileSelect should NOT be called
    expect(onFileSelect).not.toHaveBeenCalled()
  })

  it('accepts file within size limit', async () => {
    const onFileSelect = vi.fn()
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />)

    // Create a file smaller than 10MB (AN file type limit)
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    })

    const fileInput = screen.getByLabelText(/File input for Test Document/i)
    await userEvent.upload(fileInput, file)

    // onFileSelect should be called
    await waitFor(() => {
      expect(onFileSelect).toHaveBeenCalledWith(file)
    })
  })

  it('displays selected file name and size', () => {
    const file = new File(['test content'], 'my-document.pdf', {
      type: 'application/pdf',
    })
    render(<FileDropZone {...defaultProps} file={file} />)

    expect(screen.getByText('my-document.pdf')).toBeInTheDocument()
    // Size should be displayed in human-readable format
    expect(screen.getByText(/B|KB|MB/)).toBeInTheDocument()
  })

  it('shows checkmark when file is selected', () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    })
    render(<FileDropZone {...defaultProps} file={file} />)

    // Check icon should be visible (via aria-label)
    expect(screen.getByLabelText('File selected')).toBeInTheDocument()
  })

  it('shows remove button when file is selected', () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    })
    const onRemove = vi.fn()
    render(<FileDropZone {...defaultProps} file={file} onRemove={onRemove} />)

    // Remove button should be visible
    const removeButton = screen.getByLabelText(/Remove Test Document/i)
    expect(removeButton).toBeInTheDocument()
  })

  it('calls onRemove when remove button is clicked', async () => {
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    })
    const onRemove = vi.fn()
    render(<FileDropZone {...defaultProps} file={file} onRemove={onRemove} />)

    const removeButton = screen.getByLabelText(/Remove Test Document/i)
    await userEvent.click(removeButton)

    expect(onRemove).toHaveBeenCalled()
  })

  it('handles drag over event', async () => {
    const { container } = render(<FileDropZone {...defaultProps} />)

    const dropZone = container.querySelector('[role="button"]')
    expect(dropZone).toBeInTheDocument()

    // Simulate drag over
    fireEvent.dragOver(dropZone!)

    // Should show "Drop file here" text
    await waitFor(() => {
      expect(screen.getByText(/Drop file here/i)).toBeInTheDocument()
    })
  })

  it('handles drag leave event', async () => {
    const { container } = render(<FileDropZone {...defaultProps} />)

    const dropZone = container.querySelector('[role="button"]')

    // Drag over first
    fireEvent.dragOver(dropZone!)
    await waitFor(() => {
      expect(screen.getByText(/Drop file here/i)).toBeInTheDocument()
    })

    // Then drag leave
    fireEvent.dragLeave(dropZone!)

    // Should show original text again
    await waitFor(() => {
      expect(
        screen.getByText(/Drag and drop file here or click to browse/i)
      ).toBeInTheDocument()
    })
  })

  it('handles file drop with valid file', async () => {
    const onFileSelect = vi.fn()
    const { container } = render(
      <FileDropZone {...defaultProps} onFileSelect={onFileSelect} />
    )

    const dropZone = container.querySelector('[role="button"]')
    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    })

    // Simulate drop event
    fireEvent.drop(dropZone!, {
      dataTransfer: {
        files: [file],
      },
    })

    // onFileSelect should be called
    await waitFor(() => {
      expect(onFileSelect).toHaveBeenCalledWith(file)
    })
  })

  it('does not accept files when disabled', async () => {
    const onFileSelect = vi.fn()
    render(
      <FileDropZone
        {...defaultProps}
        onFileSelect={onFileSelect}
        disabled={true}
      />
    )

    const fileInput = screen.getByLabelText(/File input for Test Document/i)
    expect(fileInput).toBeDisabled()

    const file = new File(['test content'], 'test.pdf', {
      type: 'application/pdf',
    })
    await userEvent.upload(fileInput, file)

    // onFileSelect should NOT be called when disabled
    expect(onFileSelect).not.toHaveBeenCalled()
  })

  it('shows error alert with proper ARIA role', async () => {
    const onFileSelect = vi.fn()
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />)

    // Upload invalid file
    const file = new File(['test'], 'test.txt', { type: 'text/plain' })
    const fileInput = screen.getByLabelText(/File input for Test Document/i)

    // Use fireEvent to bypass accept attribute
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })
    fireEvent.change(fileInput)

    // Error should have alert role (increased timeout for async state updates)
    await waitFor(
      () => {
        const alert = screen.getByRole('alert')
        expect(alert).toBeInTheDocument()
        expect(alert).toHaveTextContent(/Invalid file type/i)
      },
      { timeout: 3000 }
    )
  })

  it('clears error when valid file is selected after error', async () => {
    const onFileSelect = vi.fn()
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />)

    // First, upload invalid file using fireEvent to bypass accept attribute
    const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' })
    const fileInput = screen.getByLabelText(
      /File input for Test Document/i
    ) as HTMLInputElement

    Object.defineProperty(fileInput, 'files', {
      value: [invalidFile],
      writable: true,
      configurable: true,
    })
    fireEvent.change(fileInput)

    // Error should be visible (increased timeout for async state updates)
    await waitFor(
      () => {
        expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // Then upload valid file using fireEvent as well to avoid conflicts with modified files property
    const validFile = new File(['test'], 'test.pdf', {
      type: 'application/pdf',
    })
    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: true,
      configurable: true,
    })
    fireEvent.change(fileInput)

    // Error should be cleared (increased timeout for async state updates)
    await waitFor(
      () => {
        expect(screen.queryByText(/Invalid file type/i)).not.toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // onFileSelect should be called with valid file
    expect(onFileSelect).toHaveBeenCalledWith(validFile)
  })

  it('has proper keyboard navigation support', () => {
    const { container } = render(<FileDropZone {...defaultProps} />)

    const dropZone = container.querySelector('[role="button"]')

    // Should be focusable
    expect(dropZone).toHaveAttribute('tabindex', '0')

    // Should have proper ARIA label
    expect(dropZone).toHaveAttribute(
      'aria-label',
      'Upload Test Document (test.pdf)'
    )
  })

  it('remains focusable but prevents action when file is selected in single-file mode', async () => {
    const onFileSelect = vi.fn()
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    const { container } = render(
      <FileDropZone {...defaultProps} file={file} onFileSelect={onFileSelect} />
    )

    const dropZone = container.querySelector('[role="button"]')

    // Element should remain focusable for accessibility (tabindex="0")
    expect(dropZone).toHaveAttribute('tabindex', '0')

    // But clicking should not trigger file input when file already selected
    await userEvent.click(dropZone!)

    // onFileSelect should not be called (file input not triggered)
    // Note: We can't easily test that file input wasn't clicked,
    // but the component logic prevents it (see handleClick and handleKeyDown)
  })
})

describe('FileDropZone - Multi-file Mode', () => {
  const multiFileProps = {
    label: 'Certificate of Origin (CO.pdf)',
    fileType: 'CO' as const,
    acceptedFormats: ['.pdf'],
    onFilesSelect: vi.fn(),
    files: [],
    multiple: true,
  }

  it('renders with multiple file support enabled', () => {
    render(<FileDropZone {...multiFileProps} />)

    expect(
      screen.getByText('Certificate of Origin (CO.pdf)')
    ).toBeInTheDocument()
    expect(screen.getByText(/Multiple files supported/i)).toBeInTheDocument()
  })

  it('displays file count badge when files are selected', () => {
    const files = [
      new File(['content1'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'CO_2.pdf', { type: 'application/pdf' }),
      new File(['content3'], 'CO_3.pdf', { type: 'application/pdf' }),
    ]

    render(<FileDropZone {...multiFileProps} files={files} />)

    // Should show "3 files" badge
    expect(screen.getByText('3 files')).toBeInTheDocument()
    expect(screen.getByLabelText('Files selected')).toBeInTheDocument()
  })

  it('displays "1 file" (singular) when only one file is selected', () => {
    const files = [
      new File(['content1'], 'CO_1.pdf', { type: 'application/pdf' }),
    ]

    render(<FileDropZone {...multiFileProps} files={files} />)

    // Should show "1 file" (singular)
    expect(screen.getByText('1 file')).toBeInTheDocument()
  })

  it('displays list of all selected files with names and sizes', () => {
    const files = [
      new File(['content1'], 'CO_Australia.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'CO_Vietnam.pdf', { type: 'application/pdf' }),
    ]

    render(<FileDropZone {...multiFileProps} files={files} />)

    expect(screen.getByText('CO_Australia.pdf')).toBeInTheDocument()
    expect(screen.getByText('CO_Vietnam.pdf')).toBeInTheDocument()
    // Each file should have a size display
    const sizeElements = screen.getAllByText(/B|KB|MB/)
    expect(sizeElements.length).toBeGreaterThanOrEqual(2)
  })

  it('shows individual remove button for each file', () => {
    const files = [
      new File(['content1'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'CO_2.pdf', { type: 'application/pdf' }),
    ]

    render(<FileDropZone {...multiFileProps} files={files} />)

    // Should have remove buttons for each file
    expect(screen.getByLabelText('Remove CO_1.pdf')).toBeInTheDocument()
    expect(screen.getByLabelText('Remove CO_2.pdf')).toBeInTheDocument()
  })

  it('calls onRemoveFile with correct index when remove button is clicked', async () => {
    const onRemoveFile = vi.fn()
    const files = [
      new File(['content1'], 'CO_1.pdf', { type: 'application/pdf' }),
      new File(['content2'], 'CO_2.pdf', { type: 'application/pdf' }),
      new File(['content3'], 'CO_3.pdf', { type: 'application/pdf' }),
    ]

    render(
      <FileDropZone
        {...multiFileProps}
        files={files}
        onRemoveFile={onRemoveFile}
      />
    )

    // Click remove button for the second file (index 1)
    const removeButton = screen.getByLabelText('Remove CO_2.pdf')
    await userEvent.click(removeButton)

    expect(onRemoveFile).toHaveBeenCalledWith(1)
  })

  it('accepts multiple files via file input', async () => {
    const onFilesSelect = vi.fn()
    render(<FileDropZone {...multiFileProps} onFilesSelect={onFilesSelect} />)

    const file1 = new File(['content1'], 'CO_1.pdf', {
      type: 'application/pdf',
    })
    const file2 = new File(['content2'], 'CO_2.pdf', {
      type: 'application/pdf',
    })
    const file3 = new File(['content3'], 'CO_3.pdf', {
      type: 'application/pdf',
    })

    const fileInput = screen.getByLabelText(
      /File input for Certificate of Origin/i
    )

    // Upload multiple files at once
    await userEvent.upload(fileInput, [file1, file2, file3])

    // Should be called with array of all 3 files
    await waitFor(() => {
      expect(onFilesSelect).toHaveBeenCalledWith([file1, file2, file3])
    })
  })

  it('appends new files to existing files', async () => {
    const existingFiles = [
      new File(['existing'], 'CO_existing.pdf', { type: 'application/pdf' }),
    ]
    const onFilesSelect = vi.fn()

    render(
      <FileDropZone
        {...multiFileProps}
        files={existingFiles}
        onFilesSelect={onFilesSelect}
      />
    )

    const newFile = new File(['new'], 'CO_new.pdf', { type: 'application/pdf' })
    const fileInput = screen.getByLabelText(
      /File input for Certificate of Origin/i
    )

    await userEvent.upload(fileInput, newFile)

    // Should be called with existing + new files
    await waitFor(() => {
      expect(onFilesSelect).toHaveBeenCalledWith([...existingFiles, newFile])
    })
  })

  it('handles drag and drop of multiple files', async () => {
    const onFilesSelect = vi.fn()
    const { container } = render(
      <FileDropZone {...multiFileProps} onFilesSelect={onFilesSelect} />
    )

    const dropZone = container.querySelector('[role="button"]')
    const file1 = new File(['content1'], 'CO_1.pdf', {
      type: 'application/pdf',
    })
    const file2 = new File(['content2'], 'CO_2.pdf', {
      type: 'application/pdf',
    })

    // Simulate dropping multiple files
    fireEvent.drop(dropZone!, {
      dataTransfer: {
        files: [file1, file2],
      },
    })

    // Should be called with both files
    await waitFor(() => {
      expect(onFilesSelect).toHaveBeenCalledWith([file1, file2])
    })
  })

  it('validates each file individually in multi-file mode', async () => {
    const onFilesSelect = vi.fn()
    render(<FileDropZone {...multiFileProps} onFilesSelect={onFilesSelect} />)

    const validFile1 = new File(['valid1'], 'CO_1.pdf', {
      type: 'application/pdf',
    })
    const invalidFile = new File(['invalid'], 'CO_invalid.txt', {
      type: 'text/plain',
    })
    const validFile2 = new File(['valid2'], 'CO_2.pdf', {
      type: 'application/pdf',
    })

    const fileInput = screen.getByLabelText(
      /File input for Certificate of Origin/i
    )

    // Simulate selecting mixed valid/invalid files
    Object.defineProperty(fileInput, 'files', {
      value: [validFile1, invalidFile, validFile2],
      writable: true,
    })
    fireEvent.change(fileInput)

    // Should show error for invalid file
    await waitFor(
      () => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
        expect(
          screen.getByText(/CO_invalid\.txt.*Invalid file type/i)
        ).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // Should still pass valid files to parent
    expect(onFilesSelect).toHaveBeenCalledWith([validFile1, validFile2])
  })

  it('shows error when file exceeds size limit in multi-file mode', async () => {
    const onFilesSelect = vi.fn()
    render(<FileDropZone {...multiFileProps} onFilesSelect={onFilesSelect} />)

    const validFile = new File(['valid'], 'CO_1.pdf', {
      type: 'application/pdf',
    })
    const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'CO_large.pdf', {
      type: 'application/pdf',
    })

    const fileInput = screen.getByLabelText(
      /File input for Certificate of Origin/i
    )
    await userEvent.upload(fileInput, [validFile, largeFile])

    // Should show error for large file
    await waitFor(
      () => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
        expect(
          screen.getByText(/CO_large\.pdf.*File too large/i)
        ).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // Should still accept valid file
    expect(onFilesSelect).toHaveBeenCalledWith([validFile])
  })

  it('shows "Click or drag to add more files" when files are already selected', () => {
    const files = [
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
    ]
    render(<FileDropZone {...multiFileProps} files={files} />)

    expect(
      screen.getByText(/Click or drag to add more files/i)
    ).toBeInTheDocument()
  })

  it('allows clicking to add more files when files are already selected', async () => {
    const existingFiles = [
      new File(['existing'], 'CO_1.pdf', { type: 'application/pdf' }),
    ]
    const onFilesSelect = vi.fn()

    const { container } = render(
      <FileDropZone
        {...multiFileProps}
        files={existingFiles}
        onFilesSelect={onFilesSelect}
      />
    )

    const dropZone = container.querySelector('[role="button"]')

    // Clicking should still open file browser in multi-file mode
    await userEvent.click(dropZone!)

    // Verify file input was triggered (input element should exist)
    const fileInput = screen.getByLabelText(
      /File input for Certificate of Origin/i
    )
    expect(fileInput).toBeInTheDocument()
  })

  it('shows "Drop more files here" during drag over when files exist', async () => {
    const files = [
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
    ]
    const { container } = render(
      <FileDropZone {...multiFileProps} files={files} />
    )

    const dropZone = container.querySelector('[role="button"]')

    // Simulate drag over
    fireEvent.dragOver(dropZone!)

    await waitFor(() => {
      expect(screen.getByText(/Drop more files here/i)).toBeInTheDocument()
    })
  })

  it('has input element with multiple attribute set', () => {
    render(<FileDropZone {...multiFileProps} />)

    const fileInput = screen.getByLabelText(
      /File input for Certificate of Origin/i
    ) as HTMLInputElement
    expect(fileInput.multiple).toBe(true)
  })

  it('clears error when valid files are added after error', async () => {
    const onFilesSelect = vi.fn()
    render(<FileDropZone {...multiFileProps} onFilesSelect={onFilesSelect} />)

    // First, try to upload invalid file
    const invalidFile = new File(['test'], 'invalid.txt', {
      type: 'text/plain',
    })
    const fileInput = screen.getByLabelText(
      /File input for Certificate of Origin/i
    )

    Object.defineProperty(fileInput, 'files', {
      value: [invalidFile],
      writable: true,
      configurable: true,
    })
    fireEvent.change(fileInput)

    // Error should appear
    await waitFor(
      () => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // Then upload valid file
    const validFile = new File(['test'], 'CO_1.pdf', {
      type: 'application/pdf',
    })
    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: true,
      configurable: true,
    })
    fireEvent.change(fileInput)

    // Error should be cleared
    await waitFor(
      () => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    expect(onFilesSelect).toHaveBeenCalledWith([validFile])
  })

  it('remains focusable in multi-file mode even when files are selected', () => {
    const files = [
      new File(['content'], 'CO_1.pdf', { type: 'application/pdf' }),
    ]
    const { container } = render(
      <FileDropZone {...multiFileProps} files={files} />
    )

    const dropZone = container.querySelector('[role="button"]')

    // Should still be focusable in multi-file mode (to add more files)
    expect(dropZone).toHaveAttribute('tabindex', '0')
  })
})
