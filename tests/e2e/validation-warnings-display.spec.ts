/**
 * E2E Test for Validation Warnings Display
 *
 * Tests the enhanced ValidationWarningsPanel component:
 * - Warning display with three severity levels (error, warning, info)
 * - Severity grouping and badge counts
 * - Expandable details functionality
 * - Jump to Source navigation
 * - Dismiss/restore warnings functionality
 * - LocalStorage persistence
 */

import { test, expect } from '@playwright/test'
import { login } from './helpers/login'

test.describe('Validation Warnings Display', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, {
      email: 'demo@example.com',
      password: 'password123',
    })
  })

  test('should display validation warnings panel with all severity levels', async ({
    page,
    context,
  }) => {
    // Create a test declaration with validation warnings
    const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'

    // Get auth token from cookie
    const cookies = await context.cookies()
    const authToken = cookies.find((c) => c.name === 'access_token')?.value

    // Create a mock declaration with validation warnings
    const createResponse = await page.request.post(
      `${apiURL}/api/v1/declarations`,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: {
          organization_id: 1,
          status: 'READY_FOR_REVIEW',
          draft_data: {
            importer: { company_name: 'Test Company' },
          },
          validation_warnings: [
            {
              message: 'Invoice total does not match sum of line items',
              severity: 'error',
              field: 'invoice.invoice_total',
              rule: 'amount_discrepancy',
              details: {
                source_docs: ['INVOICE'],
                expected_value: 10000,
                actual_value: 9500,
                confidence: 0.95,
              },
            },
            {
              message: 'Importer name differs between Invoice and BOL',
              severity: 'warning',
              field: 'importer.company_name',
              rule: 'name_variation',
              details: {
                source_docs: ['INVOICE', 'BOL'],
                expected_value: 'ACME Corp',
                actual_value: 'ACME Corporation',
                confidence: 0.85,
              },
            },
            {
              message: 'Product count differs between Invoice and CO',
              severity: 'info',
              field: 'products',
              rule: 'product_count_mismatch',
              details: {
                source_docs: ['INVOICE', 'CO'],
                expected_value: 5,
                actual_value: 4,
                confidence: 1.0,
              },
            },
          ],
        },
      }
    )

    expect(createResponse.ok()).toBe(true)
    const declaration = await createResponse.json()
    const declarationId = declaration.id

    // Navigate to review page
    await page.goto(`/declarations/${declarationId}/review`)

    // Wait for the page to load
    await page.waitForLoadState('networkidle')

    // Verify validation warnings panel is visible
    await expect(
      page.getByRole('heading', { name: /validation issues/i })
    ).toBeVisible()

    // Verify summary badges
    await expect(page.getByText(/1 error/i)).toBeVisible()
    await expect(page.getByText(/1 warning/i)).toBeVisible()
    await expect(page.getByText(/1 info/i)).toBeVisible()

    // Verify all three severity sections exist
    await expect(
      page.getByRole('heading', { name: /errors.*must be fixed/i })
    ).toBeVisible()
    await expect(
      page.getByRole('heading', { name: /warnings.*review recommended/i })
    ).toBeVisible()
    await expect(
      page.getByRole('heading', { name: /information.*for your awareness/i })
    ).toBeVisible()

    // Verify error message is displayed
    await expect(
      page.getByText(/invoice total does not match sum of line items/i)
    ).toBeVisible()

    // Verify warning message is displayed
    await expect(
      page.getByText(/importer name differs between invoice and bol/i)
    ).toBeVisible()

    // Verify info message is displayed
    await expect(
      page.getByText(/product count differs between invoice and co/i)
    ).toBeVisible()
  })

  test('should expand and collapse warning details', async ({
    page,
    context,
  }) => {
    // Create a test declaration with validation warnings
    const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'
    const cookies = await context.cookies()
    const authToken = cookies.find((c) => c.name === 'access_token')?.value

    const createResponse = await page.request.post(
      `${apiURL}/api/v1/declarations`,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: {
          organization_id: 1,
          status: 'READY_FOR_REVIEW',
          draft_data: {
            importer: { company_name: 'Test Company' },
          },
          validation_warnings: [
            {
              message: 'Test warning with details',
              severity: 'error',
              field: 'test.field',
              rule: 'test_rule',
              details: {
                source_docs: ['INVOICE'],
                expected_value: 100,
                actual_value: 90,
                confidence: 0.95,
              },
            },
          ],
        },
      }
    )

    expect(createResponse.ok()).toBe(true)
    const declaration = await createResponse.json()

    await page.goto(`/declarations/${declaration.id}/review`)
    await page.waitForLoadState('networkidle')

    // Details should not be visible initially
    await expect(page.getByText(/expected:/i)).not.toBeVisible()

    // Find and click the expand button (chevron down)
    const expandButton = page
      .locator('li')
      .filter({ hasText: 'Test warning with details' })
      .getByRole('button')
      .first()
    await expandButton.click()

    // Details should now be visible
    await expect(page.getByText(/expected:.*100/i)).toBeVisible()
    await expect(page.getByText(/actual:.*90/i)).toBeVisible()
    await expect(page.getByText(/confidence:.*95%/i)).toBeVisible()

    // Click again to collapse
    await expandButton.click()

    // Details should be hidden again
    await expect(page.getByText(/expected:/i)).not.toBeVisible()
  })

  test('should navigate to source document when clicking Jump to Source', async ({
    page,
    context,
  }) => {
    // Create a test declaration with validation warnings
    const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'
    const cookies = await context.cookies()
    const authToken = cookies.find((c) => c.name === 'access_token')?.value

    const createResponse = await page.request.post(
      `${apiURL}/api/v1/declarations`,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: {
          organization_id: 1,
          status: 'READY_FOR_REVIEW',
          draft_data: {
            importer: { company_name: 'Test Company' },
          },
          validation_warnings: [
            {
              message: 'Test warning for jump to source',
              severity: 'error',
              field: 'test.field',
              rule: 'test_rule',
              details: {
                source_docs: ['INVOICE', 'BOL'],
                expected_value: 100,
                actual_value: 90,
                confidence: 0.95,
              },
            },
          ],
        },
      }
    )

    expect(createResponse.ok()).toBe(true)
    const declaration = await createResponse.json()
    const declarationId = declaration.id

    await page.goto(`/declarations/${declarationId}/review`)
    await page.waitForLoadState('networkidle')

    // Expand the warning to see Jump to Source buttons
    const expandButton = page
      .locator('li')
      .filter({ hasText: 'Test warning for jump to source' })
      .getByRole('button')
      .first()
    await expandButton.click()

    // Click "View in INVOICE" button
    const jumpButton = page.getByRole('button', { name: /view in invoice/i })
    await expect(jumpButton).toBeVisible()
    await jumpButton.click()

    // Verify navigation to documents page with doc query param
    await expect(page).toHaveURL(
      new RegExp(`/declarations/${declarationId}/documents\\?doc=INVOICE`)
    )
  })

  test('should dismiss and restore warnings with localStorage persistence', async ({
    page,
    context,
  }) => {
    // Create a test declaration
    const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'
    const cookies = await context.cookies()
    const authToken = cookies.find((c) => c.name === 'access_token')?.value

    const createResponse = await page.request.post(
      `${apiURL}/api/v1/declarations`,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: {
          organization_id: 1,
          status: 'READY_FOR_REVIEW',
          draft_data: {
            importer: { company_name: 'Test Company' },
          },
          validation_warnings: [
            {
              message: 'First warning to dismiss',
              severity: 'error',
              field: 'test.field1',
              rule: 'test_rule_1',
            },
            {
              message: 'Second warning to keep',
              severity: 'warning',
              field: 'test.field2',
              rule: 'test_rule_2',
            },
          ],
        },
      }
    )

    expect(createResponse.ok()).toBe(true)
    const declaration = await createResponse.json()
    const declarationId = declaration.id

    await page.goto(`/declarations/${declarationId}/review`)
    await page.waitForLoadState('networkidle')

    // Verify both warnings are visible
    await expect(page.getByText(/first warning to dismiss/i)).toBeVisible()
    await expect(page.getByText(/second warning to keep/i)).toBeVisible()

    // Dismiss the first warning
    const dismissButton = page
      .locator('li')
      .filter({ hasText: 'First warning to dismiss' })
      .getByRole('button', { name: /dismiss/i })
    await dismissButton.click()

    // First warning should be hidden (not in DOM or have opacity-50)
    await expect(page.getByText(/first warning to dismiss/i)).toHaveClass(
      /opacity-50/
    )

    // Second warning should still be visible normally
    const secondWarning = page.locator('li').filter({
      hasText: 'Second warning to keep',
    })
    await expect(secondWarning).not.toHaveClass(/opacity-50/)

    // Verify "Show dismissed" button appears
    await expect(
      page.getByRole('button', { name: /show dismissed.*1/i })
    ).toBeVisible()

    // Reload the page to verify localStorage persistence
    await page.reload()
    await page.waitForLoadState('networkidle')

    // First warning should still be dismissed after reload
    await expect(page.getByText(/first warning to dismiss/i)).toHaveClass(
      /opacity-50/
    )

    // Click "Show dismissed" to see all warnings
    await page.getByRole('button', { name: /show dismissed/i }).click()

    // Now click to restore the warning
    const restoreButton = page
      .locator('li')
      .filter({ hasText: 'First warning to dismiss' })
      .getByRole('button', { name: /restore/i })
    await restoreButton.click()

    // First warning should be visible normally again
    const restoredWarning = page.locator('li').filter({
      hasText: 'First warning to dismiss',
    })
    await expect(restoredWarning).not.toHaveClass(/opacity-50/)

    // "Show dismissed" button should disappear
    await expect(
      page.getByRole('button', { name: /show dismissed/i })
    ).not.toBeVisible()
  })

  test('should correctly group warnings by severity', async ({
    page,
    context,
  }) => {
    const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'
    const cookies = await context.cookies()
    const authToken = cookies.find((c) => c.name === 'access_token')?.value

    const createResponse = await page.request.post(
      `${apiURL}/api/v1/declarations`,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: {
          organization_id: 1,
          status: 'READY_FOR_REVIEW',
          draft_data: {
            importer: { company_name: 'Test Company' },
          },
          validation_warnings: [
            {
              message: 'Error 1',
              severity: 'error',
              rule: 'error_1',
            },
            {
              message: 'Error 2',
              severity: 'error',
              rule: 'error_2',
            },
            {
              message: 'Warning 1',
              severity: 'warning',
              rule: 'warning_1',
            },
            {
              message: 'Info 1',
              severity: 'info',
              rule: 'info_1',
            },
            {
              message: 'Info 2',
              severity: 'info',
              rule: 'info_2',
            },
            {
              message: 'Info 3',
              severity: 'info',
              rule: 'info_3',
            },
          ],
        },
      }
    )

    expect(createResponse.ok()).toBe(true)
    const declaration = await createResponse.json()

    await page.goto(`/declarations/${declaration.id}/review`)
    await page.waitForLoadState('networkidle')

    // Verify badge counts
    await expect(page.getByText(/2 errors/i)).toBeVisible()
    await expect(page.getByText(/1 warning/i)).toBeVisible()
    await expect(page.getByText(/3 info/i)).toBeVisible()

    // Verify section headings with counts
    await expect(
      page.getByRole('heading', { name: /errors \(2\)/i })
    ).toBeVisible()
    await expect(
      page.getByRole('heading', { name: /warnings \(1\)/i })
    ).toBeVisible()
    await expect(
      page.getByRole('heading', { name: /information \(3\)/i })
    ).toBeVisible()

    // Verify all warnings are displayed
    await expect(page.getByText('Error 1')).toBeVisible()
    await expect(page.getByText('Error 2')).toBeVisible()
    await expect(page.getByText('Warning 1')).toBeVisible()
    await expect(page.getByText('Info 1')).toBeVisible()
    await expect(page.getByText('Info 2')).toBeVisible()
    await expect(page.getByText('Info 3')).toBeVisible()
  })
})
