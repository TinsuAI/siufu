import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import UploadPage from '@/app/upload/page';
import { useAuthStore } from '@/stores/auth-store';
import { useUploadStore } from '@/stores/upload-store';
import * as api from '@/lib/api';

// Mock Next.js navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock API module
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual('@/lib/api');
  return {
    ...actual,
    uploadDeclaration: vi.fn(),
  };
});

describe('UploadPage Integration Tests', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    mockPush.mockClear();

    // Create a new QueryClient for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // Set user as authenticated
    useAuthStore.setState({
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
      isAuthenticated: true,
      isLoading: false,
    });

    // Reset upload store
    useUploadStore.getState().reset();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
  };

  it('renders all 6 drop zones with correct labels', () => {
    renderWithProviders(<UploadPage />);

    // Check all 6 file drop zones are rendered
    expect(screen.getByText(/Arrival Notice.*AN\.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/Bill of Lading.*BOL\.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/Certificate of Origin.*CO\.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/Invoice.*INVOICE/i)).toBeInTheDocument();
    expect(screen.getByText(/Good List.*goodlist\.xlsx/i)).toBeInTheDocument();
    expect(screen.getByText(/EXIM Tariff.*tariff\.xlsx/i)).toBeInTheDocument();
  });

  it('shows page header and instructions', async () => {
    renderWithProviders(<UploadPage />);

    // Wait for page to fully render
    await waitFor(() => {
      expect(screen.getByText('Upload Declaration Documents')).toBeInTheDocument();
      expect(screen.getByText(/Upload all 6 required files to process a new customs declaration/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('shows upload progress counter', () => {
    renderWithProviders(<UploadPage />);

    // Initially should show 0 of 6
    expect(screen.getByText(/Upload Progress: 0 of 6 files uploaded/i)).toBeInTheDocument();
  });

  it('Process Declaration button is disabled when no files uploaded', () => {
    renderWithProviders(<UploadPage />);

    const processButton = screen.getByRole('button', { name: /Process declaration/i });
    expect(processButton).toBeDisabled();
  });

  it('updates progress counter when files are added', async () => {
    renderWithProviders(<UploadPage />);

    // Add one file
    const file1 = new File(['content'], 'AN.pdf', { type: 'application/pdf' });
    const fileInput1 = screen.getAllByLabelText(/File input/i)[0];
    await userEvent.upload(fileInput1, file1);

    // Progress should update to 1 of 6
    await waitFor(() => {
      expect(screen.getByText(/Upload Progress: 1 of 6 files uploaded/i)).toBeInTheDocument();
    });

    // Add another file
    const file2 = new File(['content'], 'BOL.pdf', { type: 'application/pdf' });
    const fileInput2 = screen.getAllByLabelText(/File input/i)[1];
    await userEvent.upload(fileInput2, file2);

    // Progress should update to 2 of 6
    await waitFor(() => {
      expect(screen.getByText(/Upload Progress: 2 of 6 files uploaded/i)).toBeInTheDocument();
    });
  });

  it('enables Process Declaration button when all 6 files are uploaded', async () => {
    renderWithProviders(<UploadPage />);

    // Upload all 6 files
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
      new File(['content'], 'goodlist.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
      new File(['content'], 'tariff.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
    ];

    const fileInputs = screen.getAllByLabelText(/File input/i);

    for (let i = 0; i < 6; i++) {
      await userEvent.upload(fileInputs[i], files[i]);
    }

    // Wait for all files to be processed
    await waitFor(() => {
      expect(screen.getByText(/Upload Progress: 6 of 6 files uploaded/i)).toBeInTheDocument();
    });

    // Process button should now be enabled
    const processButton = screen.getByRole('button', { name: /Process declaration/i });
    expect(processButton).not.toBeDisabled();
  });

  it('shows success message when all 6 files are uploaded', async () => {
    renderWithProviders(<UploadPage />);

    // Upload all 6 files
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
      new File(['content'], 'goodlist.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
      new File(['content'], 'tariff.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
    ];

    const fileInputs = screen.getAllByLabelText(/File input/i);

    for (let i = 0; i < 6; i++) {
      await userEvent.upload(fileInputs[i], files[i]);
    }

    // Should show "All files uploaded! Ready to process."
    await waitFor(() => {
      expect(screen.getByText(/All files uploaded! Ready to process/i)).toBeInTheDocument();
    });
  });

  it('successfully uploads files and navigates to declaration page', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration);
    mockUploadDeclaration.mockResolvedValue({
      declaration_id: 'test-declaration-123',
      status: 'UPLOADED',
      created_at: '2025-10-31T12:00:00Z',
    });

    renderWithProviders(<UploadPage />);

    // Upload all 6 files
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
      new File(['content'], 'goodlist.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
      new File(['content'], 'tariff.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
    ];

    const fileInputs = screen.getAllByLabelText(/File input/i);

    for (let i = 0; i < 6; i++) {
      await userEvent.upload(fileInputs[i], files[i]);
    }

    // Wait for all files to be uploaded
    await waitFor(() => {
      expect(screen.getByText(/6 of 6 files uploaded/i)).toBeInTheDocument();
    });

    // Click Process Declaration button
    const processButton = screen.getByRole('button', { name: /Process declaration/i });
    await userEvent.click(processButton);

    // Should call uploadDeclaration API (may be too fast to see "Uploading..." text)
    await waitFor(() => {
      expect(mockUploadDeclaration).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Should navigate to declaration page (increased timeout for async navigation)
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/declarations/test-declaration-123');
    }, { timeout: 5000 });
  });

  it('displays error message when upload fails', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration);
    mockUploadDeclaration.mockRejectedValue(new Error('Network error. Please check your connection.'));

    renderWithProviders(<UploadPage />);

    // Upload all 6 files
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
      new File(['content'], 'goodlist.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
      new File(['content'], 'tariff.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
    ];

    const fileInputs = screen.getAllByLabelText(/File input/i);

    for (let i = 0; i < 6; i++) {
      await userEvent.upload(fileInputs[i], files[i]);
    }

    // Click Process Declaration button
    await waitFor(() => {
      expect(screen.getByText(/6 of 6 files uploaded/i)).toBeInTheDocument();
    });

    const processButton = screen.getByRole('button', { name: /Process declaration/i });
    await userEvent.click(processButton);

    // Should display error message
    await waitFor(() => {
      expect(screen.getByText(/Upload Failed/i)).toBeInTheDocument();
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });

    // Should show Retry button
    expect(screen.getByRole('button', { name: /Retry Upload/i })).toBeInTheDocument();
  });

  it('allows retry after upload failure', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration);

    // First call fails
    mockUploadDeclaration.mockRejectedValueOnce(new Error('Network error'));

    // Second call succeeds
    mockUploadDeclaration.mockResolvedValueOnce({
      declaration_id: 'test-declaration-456',
      status: 'UPLOADED',
      created_at: '2025-10-31T12:00:00Z',
    });

    renderWithProviders(<UploadPage />);

    // Upload all 6 files
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
      new File(['content'], 'goodlist.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
      new File(['content'], 'tariff.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
    ];

    const fileInputs = screen.getAllByLabelText(/File input/i);

    for (let i = 0; i < 6; i++) {
      await userEvent.upload(fileInputs[i], files[i]);
    }

    // Click Process Declaration (first attempt - fails)
    await waitFor(() => {
      expect(screen.getByText(/6 of 6 files uploaded/i)).toBeInTheDocument();
    });

    const processButton = screen.getByRole('button', { name: /Process declaration/i });
    await userEvent.click(processButton);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/Upload Failed/i)).toBeInTheDocument();
    });

    // Click Retry button
    const retryButton = screen.getByRole('button', { name: /Retry Upload/i });
    await userEvent.click(retryButton);

    // Second attempt should succeed and navigate
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/declarations/test-declaration-456');
    });
  });

  it('redirects to login if user is not authenticated', async () => {
    // Set user as not authenticated
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });

    renderWithProviders(<UploadPage />);

    // Should redirect to login
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  it('disables all drop zones while upload is in progress', async () => {
    const mockUploadDeclaration = vi.mocked(api.uploadDeclaration);

    // Make upload take a while (simulate slow network)
    mockUploadDeclaration.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                declaration_id: 'test-declaration-789',
                status: 'UPLOADED',
                created_at: '2025-10-31T12:00:00Z',
              }),
            1000
          )
        )
    );

    renderWithProviders(<UploadPage />);

    // Upload all 6 files
    const files = [
      new File(['content'], 'AN.pdf', { type: 'application/pdf' }),
      new File(['content'], 'BOL.pdf', { type: 'application/pdf' }),
      new File(['content'], 'CO.pdf', { type: 'application/pdf' }),
      new File(['content'], 'INVOICE.pdf', { type: 'application/pdf' }),
      new File(['content'], 'goodlist.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
      new File(['content'], 'tariff.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }),
    ];

    const fileInputs = screen.getAllByLabelText(/File input/i);

    for (let i = 0; i < 6; i++) {
      await userEvent.upload(fileInputs[i], files[i]);
    }

    await waitFor(() => {
      expect(screen.getByText(/6 of 6 files uploaded/i)).toBeInTheDocument();
    });

    // Click Process Declaration
    const processButton = screen.getByRole('button', { name: /Process declaration/i });
    await userEvent.click(processButton);

    // While uploading, all file inputs should be disabled
    await waitFor(() => {
      expect(screen.getByText(/Uploading\.\.\./i)).toBeInTheDocument();
    });

    const fileInputsAfterUpload = screen.getAllByLabelText(/File input/i);
    fileInputsAfterUpload.forEach((input) => {
      expect(input).toBeDisabled();
    });
  });

  it('shows help section with tips', () => {
    renderWithProviders(<UploadPage />);

    expect(screen.getByText(/Help & Tips/i)).toBeInTheDocument();
    expect(screen.getByText(/You can drag and drop files/i)).toBeInTheDocument();
    expect(screen.getByText(/Files are validated for type and size/i)).toBeInTheDocument();
    expect(screen.getByText(/Maximum file sizes/i)).toBeInTheDocument();
  });
});
