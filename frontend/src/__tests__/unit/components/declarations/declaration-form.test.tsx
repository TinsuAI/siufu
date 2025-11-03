/**
 * DeclarationForm Component Tests
 *
 * Tests for the declaration review form component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DeclarationForm } from '@/components/declarations/declaration-form'
import type { DraftData } from '@/types/declaration'

describe('DeclarationForm', () => {
  const mockInitialData: DraftData = {
    company_info: {
      importer_name: 'Test Company',
      tax_id: '1234567890',
      address: '123 Main St',
      city: 'Test City',
      country: 'US',
      contact_person: 'John Doe',
      contact_email: 'john@example.com',
      contact_phone: '+1234567890',
    },
    shipment_details: {
      bol_number: 'BOL123',
      arrival_date: '2025-01-15',
      port_of_arrival: 'Port A',
      port_of_departure: 'Port B',
      container_numbers: ['CONT001'],
      vessel_name: 'Test Vessel',
    },
    products: [
      {
        description: 'Test Product',
        hs_code: '12345678',
        quantity: 10,
        unit: 'kg',
        unit_price: 100,
        total_price: 1000,
        origin_country: 'CN',
      },
    ],
    tax_calculations: {
      subtotal: 1000,
      vat_rate: 10,
      vat_amount: 100,
      import_duty_rate: 5,
      import_duty_amount: 50,
      total_tax: 150,
      grand_total: 1150,
    },
  }

  const mockConfidenceScores = {
    'company_info.importer_name': 0.95,
    'company_info.tax_id': 0.85,
    'products.0.hs_code': 0.65,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('renders all 4 form sections', () => {
      render(
        <DeclarationForm
          initialData={mockInitialData}
          confidenceScores={mockConfidenceScores}
        />
      )

      expect(screen.getByText('Company Information')).toBeInTheDocument()
      expect(screen.getByText('Shipment Details')).toBeInTheDocument()
      expect(screen.getByText('Product Line Items')).toBeInTheDocument()
      expect(screen.getByText('Tax Calculations')).toBeInTheDocument()
    })

    it('renders form fields with initial data', () => {
      render(
        <DeclarationForm
          initialData={mockInitialData}
          confidenceScores={mockConfidenceScores}
        />
      )

      expect(screen.getByDisplayValue('Test Company')).toBeInTheDocument()
      expect(screen.getByDisplayValue('1234567890')).toBeInTheDocument()
      expect(screen.getByDisplayValue('BOL123')).toBeInTheDocument()
    })

    it('renders empty form when no initial data provided', () => {
      render(<DeclarationForm />)

      const importerNameInput = screen.getByPlaceholderText(
        'Enter importer name'
      )
      expect(importerNameInput).toBeInTheDocument()
      expect(importerNameInput).toHaveValue('')
    })
  })

  describe('Confidence Color Coding', () => {
    it('applies green border for high confidence fields (>90%)', () => {
      render(
        <DeclarationForm
          initialData={mockInitialData}
          confidenceScores={{ 'company_info.importer_name': 0.95 }}
        />
      )

      const importerNameInput = screen.getByDisplayValue('Test Company')
      expect(importerNameInput).toHaveClass('border-green-500')
    })

    it('applies yellow border for medium confidence fields (70-90%)', () => {
      render(
        <DeclarationForm
          initialData={mockInitialData}
          confidenceScores={{ 'company_info.tax_id': 0.85 }}
        />
      )

      const taxIdInput = screen.getByDisplayValue('1234567890')
      expect(taxIdInput).toHaveClass('border-yellow-500')
    })

    it('applies red border for low confidence fields (<70%)', () => {
      render(
        <DeclarationForm
          initialData={mockInitialData}
          confidenceScores={{ 'products.0.hs_code': 0.65 }}
        />
      )

      const hsCodeInput = screen.getByDisplayValue('12345678')
      expect(hsCodeInput).toHaveClass('border-red-500')
    })
  })

  describe('Form Validation', () => {
    it.skip('displays validation error for invalid email', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()

      render(
        <DeclarationForm initialData={mockInitialData} onSubmit={onSubmit} />
      )

      // Find and clear the email input
      const emailInput = screen.getByLabelText(/contact email/i)
      await user.clear(emailInput)
      await user.type(emailInput, 'invalid-email')

      // Trigger form submission
      const submitButton = screen.getByText('Save Declaration')
      await user.click(submitButton)

      // Wait for validation error to appear
      await waitFor(
        () => {
          const errorElements = screen.queryAllByText(/invalid/i)
          expect(errorElements.length).toBeGreaterThan(0)
        },
        { timeout: 3000 }
      )

      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('displays validation error for invalid HS code', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()

      render(
        <DeclarationForm initialData={mockInitialData} onSubmit={onSubmit} />
      )

      const hsCodeInput = screen.getByDisplayValue('12345678')
      await user.clear(hsCodeInput)
      await user.type(hsCodeInput, '123') // Too short

      const submitButton = screen.getByText('Save Declaration')
      await user.click(submitButton)

      await waitFor(() => {
        expect(
          screen.getByText('HS Code must be exactly 8 digits')
        ).toBeInTheDocument()
      })

      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('displays validation error for required fields', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()

      render(<DeclarationForm onSubmit={onSubmit} />)

      const submitButton = screen.getByText('Save Declaration')
      await user.click(submitButton)

      await waitFor(() => {
        expect(
          screen.getByText('Importer name is required')
        ).toBeInTheDocument()
      })

      expect(onSubmit).not.toHaveBeenCalled()
    })
  })

  describe('Product Line Items', () => {
    it('allows adding new product rows', async () => {
      const user = userEvent.setup()

      render(<DeclarationForm initialData={mockInitialData} />)

      const addButton = screen.getByText('Add Product')
      await user.click(addButton)

      const productRows = screen.getAllByPlaceholderText('Product description')
      expect(productRows).toHaveLength(2) // Initial + added
    })

    it('allows removing product rows', async () => {
      const user = userEvent.setup()

      const dataWith2Products: DraftData = {
        ...mockInitialData,
        products: [
          ...mockInitialData.products,
          {
            description: 'Product 2',
            hs_code: '87654321',
            quantity: 5,
            unit: 'pcs',
            unit_price: 50,
            total_price: 250,
            origin_country: 'US',
          },
        ],
      }

      render(<DeclarationForm initialData={dataWith2Products} />)

      const productRows = screen.getAllByPlaceholderText('Product description')
      expect(productRows).toHaveLength(2)

      // Use aria-label to find delete button
      const deleteButton = screen.getByRole('button', {
        name: 'Remove product 1',
      })
      expect(deleteButton).toBeInTheDocument()

      await user.click(deleteButton)

      await waitFor(() => {
        const updatedProductRows = screen.getAllByPlaceholderText(
          'Product description'
        )
        expect(updatedProductRows).toHaveLength(1)
      })
    })

    it('prevents removing the last product row', () => {
      render(<DeclarationForm initialData={mockInitialData} />)

      // Should not have any delete buttons when only 1 product
      const deleteButton = screen.queryByRole('button', {
        name: /Remove product/i,
      })
      expect(deleteButton).not.toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    it('calls onSubmit with valid form data', async () => {
      const user = userEvent.setup()
      const onSubmit = vi.fn()

      render(
        <DeclarationForm initialData={mockInitialData} onSubmit={onSubmit} />
      )

      const submitButton = screen.getByText('Save Declaration')
      await user.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            company_info: expect.objectContaining({
              importer_name: 'Test Company',
            }),
          })
        )
      })
    })

    it('does not render submit button when onSubmit not provided', () => {
      render(<DeclarationForm initialData={mockInitialData} />)

      expect(screen.queryByText('Save Declaration')).not.toBeInTheDocument()
    })
  })

  describe('Form Change Callback', () => {
    it('calls onChange when form data changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()

      render(
        <DeclarationForm initialData={mockInitialData} onChange={onChange} />
      )

      const importerNameInput = screen.getByDisplayValue('Test Company')
      await user.clear(importerNameInput)
      await user.type(importerNameInput, 'New Company Name')

      await waitFor(() => {
        expect(onChange).toHaveBeenCalled()
      })
    })
  })

  describe('Collapsible Sections', () => {
    it('starts with all sections open by default', () => {
      render(<DeclarationForm initialData={mockInitialData} />)

      // All sections should be visible
      expect(
        screen.getByPlaceholderText('Enter importer name')
      ).toBeInTheDocument()
      expect(
        screen.getByPlaceholderText('Enter BOL number')
      ).toBeInTheDocument()
      expect(
        screen.getByPlaceholderText('Product description')
      ).toBeInTheDocument()
    })

    it('allows collapsing and expanding sections', async () => {
      const user = userEvent.setup()

      render(<DeclarationForm initialData={mockInitialData} />)

      // Find the collapsible trigger button (the entire header is clickable)
      const companyHeader = screen.getByText('Company Information')

      // Click to collapse
      await user.click(companyHeader)

      // After collapse, the content should have data-state="closed" or be hidden
      // Since radix-ui collapsible uses data-state, let's wait for that
      await waitFor(
        () => {
          const importerInput = screen.queryByPlaceholderText(
            'Enter importer name'
          )
          // The input might still be in DOM but hidden via CSS
          // Let's check if it's not visible or the parent collapsible is closed
          if (importerInput) {
            const collapsibleContent = importerInput.closest('[data-state]')
            if (collapsibleContent) {
              expect(collapsibleContent).toHaveAttribute('data-state', 'closed')
            } else {
              // If no data-state, just check visibility
              expect(importerInput).not.toBeVisible()
            }
          }
        },
        { timeout: 3000 }
      )
    })
  })

  describe('Container Numbers Management', () => {
    it('allows adding new container numbers', async () => {
      const user = userEvent.setup()

      render(<DeclarationForm initialData={mockInitialData} />)

      const addContainerButton = screen.getByText('Add Container')
      await user.click(addContainerButton)

      const containerInputs = screen.getAllByPlaceholderText(/Container \d+/)
      expect(containerInputs).toHaveLength(2)
    })

    it('allows removing container numbers', async () => {
      const user = userEvent.setup()

      const dataWith2Containers: DraftData = {
        ...mockInitialData,
        shipment_details: {
          ...mockInitialData.shipment_details,
          container_numbers: ['CONT001', 'CONT002'],
        },
      }

      render(<DeclarationForm initialData={dataWith2Containers} />)

      const containerInputs = screen.getAllByPlaceholderText(/Container \d+/)
      expect(containerInputs).toHaveLength(2)

      // Use aria-label to find delete button
      const deleteButton = screen.getByRole('button', {
        name: 'Remove container 1',
      })
      expect(deleteButton).toBeInTheDocument()

      await user.click(deleteButton)

      await waitFor(() => {
        const updatedContainerInputs =
          screen.getAllByPlaceholderText(/Container \d+/)
        expect(updatedContainerInputs).toHaveLength(1)
      })
    })
  })
})
