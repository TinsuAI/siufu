/**
 * Unit tests for DeclarationForm component
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { DeclarationForm, DeclarationFormData } from '@/components/declarations/declaration-form'

describe('DeclarationForm', () => {
  it('renders form with all required fields', () => {
    const mockSubmit = vi.fn()
    render(<DeclarationForm onSubmit={mockSubmit} />)

    // Check for form labels using accessible queries
    expect(screen.getByLabelText(/importer name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/importer address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/total value/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/currency/i)).toBeInTheDocument()

    // Check for submit button
    expect(screen.getByRole('button', { name: /submit declaration/i })).toBeInTheDocument()
  })

  it('displays validation errors for empty required fields', async () => {
    const user = userEvent.setup()
    const mockSubmit = vi.fn()
    render(<DeclarationForm onSubmit={mockSubmit} />)

    // Click submit without filling any fields
    const submitButton = screen.getByRole('button', { name: /submit declaration/i })
    await user.click(submitButton)

    // Wait for validation errors to appear
    await waitFor(() => {
      expect(screen.getByText(/importer name is required/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/importer address is required/i)).toBeInTheDocument()

    // Form should not have been submitted
    expect(mockSubmit).not.toHaveBeenCalled()
  })

  it('submits form data when all fields are valid', async () => {
    const user = userEvent.setup()
    const mockSubmit = vi.fn()
    render(<DeclarationForm onSubmit={mockSubmit} />)

    // Fill out the form
    await user.type(screen.getByLabelText(/importer name/i), 'ABC Import Corp')
    await user.type(screen.getByLabelText(/importer address/i), '123 Business Street')
    await user.type(screen.getByLabelText(/total value/i), '10500.50')
    await user.selectOptions(screen.getByLabelText(/currency/i), 'USD')

    // Submit the form
    await user.click(screen.getByRole('button', { name: /submit declaration/i }))

    // Wait for form submission
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledTimes(1)
    })

    // Check submitted data
    const submittedData: DeclarationFormData = mockSubmit.mock.calls[0][0]
    expect(submittedData.importerName).toBe('ABC Import Corp')
    expect(submittedData.importerAddress).toBe('123 Business Street')
    expect(submittedData.totalValue).toBe(10500.50)
    expect(submittedData.currency).toBe('USD')
  })

  it('populates form with initial data', () => {
    const mockSubmit = vi.fn()
    const initialData = {
      importerName: 'XYZ Trading Ltd',
      importerAddress: '456 Commerce Ave',
      totalValue: 5000,
      currency: 'EUR' as const
    }

    render(<DeclarationForm onSubmit={mockSubmit} initialData={initialData} />)

    // Check that fields are pre-filled
    expect(screen.getByLabelText(/importer name/i)).toHaveValue('XYZ Trading Ltd')
    expect(screen.getByLabelText(/importer address/i)).toHaveValue('456 Commerce Ave')
    expect(screen.getByLabelText(/total value/i)).toHaveValue(5000)
    expect(screen.getByLabelText(/currency/i)).toHaveValue('EUR')
  })

  it('disables submit button when isSubmitting is true', () => {
    const mockSubmit = vi.fn()
    render(<DeclarationForm onSubmit={mockSubmit} isSubmitting={true} />)

    const submitButton = screen.getByRole('button', { name: /submitting/i })
    expect(submitButton).toBeDisabled()
    expect(submitButton).toHaveTextContent('Submitting...')
  })

  it('validates total value must be positive', async () => {
    const user = userEvent.setup()
    const mockSubmit = vi.fn()
    render(<DeclarationForm onSubmit={mockSubmit} />)

    // Fill out form with negative value
    await user.type(screen.getByLabelText(/importer name/i), 'Test Corp')
    await user.type(screen.getByLabelText(/importer address/i), 'Test Address')
    await user.type(screen.getByLabelText(/total value/i), '-100')
    await user.selectOptions(screen.getByLabelText(/currency/i), 'USD')

    // Submit the form
    await user.click(screen.getByRole('button', { name: /submit declaration/i }))

    // Wait for validation error
    await waitFor(() => {
      expect(screen.getByText(/total value must be positive/i)).toBeInTheDocument()
    })

    expect(mockSubmit).not.toHaveBeenCalled()
  })

  it('validates currency selection', async () => {
    const user = userEvent.setup()
    const mockSubmit = vi.fn()
    render(<DeclarationForm onSubmit={mockSubmit} />)

    // Fill out form but don't select currency
    await user.type(screen.getByLabelText(/importer name/i), 'Test Corp')
    await user.type(screen.getByLabelText(/importer address/i), 'Test Address')
    await user.type(screen.getByLabelText(/total value/i), '1000')

    // Submit without selecting currency
    await user.click(screen.getByRole('button', { name: /submit declaration/i }))

    // Wait for validation error
    await waitFor(() => {
      expect(screen.getByText(/please select a valid currency/i)).toBeInTheDocument()
    })

    expect(mockSubmit).not.toHaveBeenCalled()
  })
})
