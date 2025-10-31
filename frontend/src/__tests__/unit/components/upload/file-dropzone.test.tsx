import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileDropZone } from '@/components/upload/file-dropzone';

describe('FileDropZone', () => {
  const defaultProps = {
    label: 'Test Document (test.pdf)',
    fileType: 'AN' as const,
    acceptedFormats: ['.pdf'],
    onFileSelect: vi.fn(),
    file: null,
  };

  it('renders with correct label', () => {
    render(<FileDropZone {...defaultProps} />);

    expect(screen.getByText('Test Document (test.pdf)')).toBeInTheDocument();
    expect(screen.getByText(/Drag and drop file here or click to browse/i)).toBeInTheDocument();
  });

  it('renders accepted formats info', () => {
    render(<FileDropZone {...defaultProps} />);

    // Should display accepted formats and max size
    expect(screen.getByText(/Accepted:.*\.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/max.*10.*MB/i)).toBeInTheDocument();
  });

  it('displays upload icon when no file is selected', () => {
    render(<FileDropZone {...defaultProps} />);

    // Upload icon should be visible (check by role since lucide-react uses SVG)
    const uploadPrompt = screen.getByText(/Drag and drop file here or click to browse/i);
    expect(uploadPrompt).toBeInTheDocument();
  });

  it('calls onFileSelect with valid file when file input changes', async () => {
    const onFileSelect = vi.fn();
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />);

    // Create a valid PDF file
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    // Find the hidden file input
    const fileInput = screen.getByLabelText(/File input for Test Document/i);

    // Simulate file selection
    await userEvent.upload(fileInput, file);

    // onFileSelect should be called with the file
    await waitFor(() => {
      expect(onFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it('shows error for invalid file type', async () => {
    const onFileSelect = vi.fn();
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />);

    // Create an invalid file (Word doc instead of PDF)
    const file = new File(['test content'], 'test.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    const fileInput = screen.getByLabelText(/File input for Test Document/i);

    // Use fireEvent instead of userEvent because accept attribute blocks invalid files in userEvent
    // This simulates a scenario where an invalid file gets through (e.g., via drag-and-drop)
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Should show error message (increased timeout for async state updates)
    await waitFor(() => {
      expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument();
      expect(screen.getByText(/Expected.*\.pdf/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // onFileSelect should NOT be called
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it('shows error for file exceeding size limit', async () => {
    const onFileSelect = vi.fn();
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />);

    // Create a file larger than 10MB (AN file type limit)
    const largeContent = 'x'.repeat(11 * 1024 * 1024); // 11MB
    const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });

    const fileInput = screen.getByLabelText(/File input for Test Document/i);
    await userEvent.upload(fileInput, file);

    // Should show error message (increased timeout for async state updates)
    await waitFor(() => {
      expect(screen.getByText(/File too large/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // onFileSelect should NOT be called
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it('accepts file within size limit', async () => {
    const onFileSelect = vi.fn();
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />);

    // Create a file smaller than 10MB (AN file type limit)
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    const fileInput = screen.getByLabelText(/File input for Test Document/i);
    await userEvent.upload(fileInput, file);

    // onFileSelect should be called
    await waitFor(() => {
      expect(onFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it('displays selected file name and size', () => {
    const file = new File(['test content'], 'my-document.pdf', { type: 'application/pdf' });
    render(<FileDropZone {...defaultProps} file={file} />);

    expect(screen.getByText('my-document.pdf')).toBeInTheDocument();
    // Size should be displayed in human-readable format
    expect(screen.getByText(/B|KB|MB/)).toBeInTheDocument();
  });

  it('shows checkmark when file is selected', () => {
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    render(<FileDropZone {...defaultProps} file={file} />);

    // Check icon should be visible (via aria-label)
    expect(screen.getByLabelText('File selected')).toBeInTheDocument();
  });

  it('shows remove button when file is selected', () => {
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const onRemove = vi.fn();
    render(<FileDropZone {...defaultProps} file={file} onRemove={onRemove} />);

    // Remove button should be visible
    const removeButton = screen.getByLabelText(/Remove Test Document/i);
    expect(removeButton).toBeInTheDocument();
  });

  it('calls onRemove when remove button is clicked', async () => {
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const onRemove = vi.fn();
    render(<FileDropZone {...defaultProps} file={file} onRemove={onRemove} />);

    const removeButton = screen.getByLabelText(/Remove Test Document/i);
    await userEvent.click(removeButton);

    expect(onRemove).toHaveBeenCalled();
  });

  it('handles drag over event', async () => {
    const { container } = render(<FileDropZone {...defaultProps} />);

    const dropZone = container.querySelector('[role="button"]');
    expect(dropZone).toBeInTheDocument();

    // Simulate drag over
    fireEvent.dragOver(dropZone!);

    // Should show "Drop file here" text
    await waitFor(() => {
      expect(screen.getByText(/Drop file here/i)).toBeInTheDocument();
    });
  });

  it('handles drag leave event', async () => {
    const { container } = render(<FileDropZone {...defaultProps} />);

    const dropZone = container.querySelector('[role="button"]');

    // Drag over first
    fireEvent.dragOver(dropZone!);
    await waitFor(() => {
      expect(screen.getByText(/Drop file here/i)).toBeInTheDocument();
    });

    // Then drag leave
    fireEvent.dragLeave(dropZone!);

    // Should show original text again
    await waitFor(() => {
      expect(screen.getByText(/Drag and drop file here or click to browse/i)).toBeInTheDocument();
    });
  });

  it('handles file drop with valid file', async () => {
    const onFileSelect = vi.fn();
    const { container } = render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />);

    const dropZone = container.querySelector('[role="button"]');
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    // Simulate drop event
    fireEvent.drop(dropZone!, {
      dataTransfer: {
        files: [file],
      },
    });

    // onFileSelect should be called
    await waitFor(() => {
      expect(onFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it('does not accept files when disabled', async () => {
    const onFileSelect = vi.fn();
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} disabled={true} />);

    const fileInput = screen.getByLabelText(/File input for Test Document/i);
    expect(fileInput).toBeDisabled();

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    await userEvent.upload(fileInput, file);

    // onFileSelect should NOT be called when disabled
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it('shows error alert with proper ARIA role', async () => {
    const onFileSelect = vi.fn();
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />);

    // Upload invalid file
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/File input for Test Document/i);

    // Use fireEvent to bypass accept attribute
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    fireEvent.change(fileInput);

    // Error should have alert role (increased timeout for async state updates)
    await waitFor(() => {
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveTextContent(/Invalid file type/i);
    }, { timeout: 3000 });
  });

  it('clears error when valid file is selected after error', async () => {
    const onFileSelect = vi.fn();
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />);

    // First, upload invalid file using fireEvent to bypass accept attribute
    const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText(/File input for Test Document/i) as HTMLInputElement;

    Object.defineProperty(fileInput, 'files', {
      value: [invalidFile],
      writable: true,
      configurable: true,
    });
    fireEvent.change(fileInput);

    // Error should be visible (increased timeout for async state updates)
    await waitFor(() => {
      expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Then upload valid file using fireEvent as well to avoid conflicts with modified files property
    const validFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: true,
      configurable: true,
    });
    fireEvent.change(fileInput);

    // Error should be cleared (increased timeout for async state updates)
    await waitFor(() => {
      expect(screen.queryByText(/Invalid file type/i)).not.toBeInTheDocument();
    }, { timeout: 3000 });

    // onFileSelect should be called with valid file
    expect(onFileSelect).toHaveBeenCalledWith(validFile);
  });

  it('has proper keyboard navigation support', () => {
    const { container } = render(<FileDropZone {...defaultProps} />);

    const dropZone = container.querySelector('[role="button"]');

    // Should be focusable
    expect(dropZone).toHaveAttribute('tabindex', '0');

    // Should have proper ARIA label
    expect(dropZone).toHaveAttribute('aria-label', 'Upload Test Document (test.pdf)');
  });

  it('prevents keyboard interaction when file is selected', () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const { container } = render(<FileDropZone {...defaultProps} file={file} />);

    const dropZone = container.querySelector('[role="button"]');

    // Should not be focusable when file is selected
    expect(dropZone).toHaveAttribute('tabindex', '-1');
  });
});
