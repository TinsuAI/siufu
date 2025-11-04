/**
 * E2E Test for Declaration Approval & Export Flow
 *
 * Tests Story 3.8:
 * - Approve declarations with auto-save check
 * - Reject declarations with reason
 * - Export approved declarations to Excel
 * - Status badge display on declarations list
 */

import { test, expect, Page } from '@playwright/test'
import { login } from './helpers/login'

/**
 * Helper to create a mock declaration in READY_FOR_REVIEW status
 * In a real scenario, this would go through upload/process flow
 */
async function navigateToReviewPage(page: Page): Promise<string> {
  // Navigate to declarations list
  await page.goto('/declarations')

  // Find a declaration in READY_FOR_REVIEW status
  // (In production, we'd create one through the full workflow)
  const reviewButton = page.getByRole('button', { name: /review/i }).first()
  await reviewButton.click()

  // Extract declaration ID from URL
  await page.waitForURL(/\/declarations\/[^/]+\/review/)
  const url = page.url()
  const declarationId = url.match(/\/declarations\/([^/]+)\/review/)?.[1]

  return declarationId || ''
}

/**
 * Helper to wait for auto-save to complete
 */
async function waitForAutoSaveComplete(page: Page) {
  // Wait for "Saving..." indicator to disappear
  const savingIndicator = page.getByText(/saving/i)
  const isVisible = await savingIndicator.isVisible().catch(() => false)

  if (isVisible) {
    await expect(savingIndicator).not.toBeVisible({ timeout: 10000 })
  }

  // Wait for "Saved" indicator to appear
  await expect(page.getByText(/saved/i)).toBeVisible({ timeout: 5000 })
}

test.describe('Declaration Approval Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await login(page, {
      email: 'demo@example.com',
      password: 'password123'
    })
  })

  test('should complete full approval flow with Excel download', async ({ page }) => {
    // Navigate to a declaration in review status
    const declarationId = await navigateToReviewPage(page)
    expect(declarationId).toBeTruthy()

    // Verify we're on the review page with sticky header
    await expect(page.getByRole('heading', { name: /review declaration/i })).toBeVisible()

    // Verify approve and reject buttons are visible in sticky header
    const approveButton = page.getByRole('button', { name: /approve/i })
    const rejectButton = page.getByRole('button', { name: /reject/i })

    await expect(approveButton).toBeVisible()
    await expect(rejectButton).toBeVisible()

    // Make a small edit to trigger auto-save
    await page.getByLabel(/importer.*name/i).first().fill('Updated Importer Name')

    // Verify approve button is disabled during auto-save
    await expect(approveButton).toBeDisabled({ timeout: 2000 })

    // Hover over disabled button to check for tooltip
    await approveButton.hover()
    await expect(page.getByText(/please wait for auto-save/i)).toBeVisible()

    // Wait for auto-save to complete
    await waitForAutoSaveComplete(page)

    // Verify approve button is now enabled
    await expect(approveButton).toBeEnabled({ timeout: 5000 })

    // Click approve button
    await approveButton.click()

    // Wait for approval success toast
    await expect(page.getByText(/declaration approved successfully/i)).toBeVisible({ timeout: 10000 })

    // Verify "Download Excel" button appears
    const downloadButton = page.getByRole('button', { name: /download.*excel/i })
    await expect(downloadButton).toBeVisible({ timeout: 5000 })

    // Verify approve button is no longer visible
    await expect(approveButton).not.toBeVisible()

    // Test Excel download
    const downloadPromise = page.waitForEvent('download')
    await downloadButton.click()

    // Wait for download to start
    const download = await downloadPromise

    // Verify filename matches expected pattern: CD_{declarationId}.xlsx
    const filename = download.suggestedFilename()
    expect(filename).toMatch(/CD_.*\.xlsx$/i)
    expect(filename).toContain(declarationId)

    // Verify download completes successfully
    expect(await download.failure()).toBeNull()

    // Verify success message after download
    await expect(page.getByText(/declaration approved and exported successfully/i)).toBeVisible({ timeout: 5000 })

    // Navigate to declarations list to verify status
    await page.goto('/declarations')

    // Find the approved declaration and verify status badge
    const declarationRow = page.locator(`[data-testid="declaration-${declarationId}"]`)
    await expect(declarationRow.getByText(/approved/i)).toBeVisible()

    // Verify status badge has correct styling (green)
    const statusBadge = declarationRow.locator('[data-testid="status-badge"]')
    await expect(statusBadge).toHaveClass(/bg-green/i)
  })

  test('should reject declaration with validation', async ({ page }) => {
    // Navigate to a declaration in review status
    const declarationId = await navigateToReviewPage(page)
    expect(declarationId).toBeTruthy()

    // Click reject button
    const rejectButton = page.getByRole('button', { name: /reject/i })
    await rejectButton.click()

    // Verify rejection dialog appears
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByText(/rejection reason/i)).toBeVisible()

    // Test validation: Try submitting with empty reason
    const submitButton = page.getByRole('button', { name: /submit|confirm/i })
    await submitButton.click()

    // Verify validation error appears
    await expect(page.getByText(/reason.*required|must.*provide.*reason/i)).toBeVisible()

    // Test validation: Try submitting with too short reason (< 10 chars)
    const reasonTextarea = page.getByRole('textbox', { name: /reason/i })
    await reasonTextarea.fill('Too short')
    await submitButton.click()

    // Verify minimum length validation error
    await expect(page.getByText(/at least 10 characters/i)).toBeVisible()

    // Submit with valid reason
    await reasonTextarea.fill('Incorrect customs codes detected in the declaration')
    await submitButton.click()

    // Wait for rejection success toast
    await expect(page.getByText(/declaration rejected.*reason recorded/i)).toBeVisible({ timeout: 10000 })

    // Verify redirect to declarations list
    await page.waitForURL(/\/declarations$/, { timeout: 5000 })

    // Find the rejected declaration and verify status badge
    const declarationRow = page.locator(`[data-testid="declaration-${declarationId}"]`)
    await expect(declarationRow.getByText(/rejected/i)).toBeVisible()

    // Verify status badge has correct styling (red)
    const statusBadge = declarationRow.locator('[data-testid="status-badge"]')
    await expect(statusBadge).toHaveClass(/bg-red/i)

    // Test rejection reason tooltip
    await statusBadge.hover()
    await expect(page.getByText(/incorrect customs codes/i)).toBeVisible()
  })

  test('should filter declarations by approved status', async ({ page }) => {
    // Navigate to declarations list
    await page.goto('/declarations')

    // Find and click status filter dropdown
    const statusFilter = page.getByRole('combobox', { name: /status/i })
    await statusFilter.click()

    // Select "Approved" option
    await page.getByRole('option', { name: /approved/i }).click()

    // Verify only approved declarations are shown
    const declarationRows = page.locator('[data-testid^="declaration-"]')
    const count = await declarationRows.count()

    for (let i = 0; i < count; i++) {
      const row = declarationRows.nth(i)
      await expect(row.getByText(/approved/i)).toBeVisible()
    }

    // Select "Rejected" option
    await statusFilter.click()
    await page.getByRole('option', { name: /rejected/i }).click()

    // Verify only rejected declarations are shown
    const rejectedCount = await declarationRows.count()

    for (let i = 0; i < rejectedCount; i++) {
      const row = declarationRows.nth(i)
      await expect(row.getByText(/rejected/i)).toBeVisible()
    }
  })

  test('should not allow downloading unapproved declarations', async ({ page }) => {
    // Navigate to a declaration in READY_FOR_REVIEW status
    const declarationId = await navigateToReviewPage(page)

    // Verify download button is not visible before approval
    const downloadButton = page.getByRole('button', { name: /download.*excel/i })
    await expect(downloadButton).not.toBeVisible()

    // Try to directly access export endpoint (should fail)
    const response = await page.request.get(`/api/declarations/${declarationId}/export`)
    expect(response.status()).toBe(403) // Forbidden
  })

  test('should handle approval error gracefully', async ({ page }) => {
    // Navigate to review page
    await navigateToReviewPage(page)

    // Intercept approve API call and return error
    await page.route('**/api/declarations/*/approve', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error during approval' })
      })
    })

    // Click approve button
    const approveButton = page.getByRole('button', { name: /approve/i })
    await approveButton.click()

    // Verify error toast appears
    await expect(page.getByText(/failed to approve|approval failed/i)).toBeVisible({ timeout: 5000 })

    // Verify approve button is still visible (can retry)
    await expect(approveButton).toBeVisible()

    // Verify download button does not appear
    const downloadButton = page.getByRole('button', { name: /download.*excel/i })
    await expect(downloadButton).not.toBeVisible()
  })

  test('should verify sticky header remains visible while scrolling', async ({ page }) => {
    // Navigate to review page
    await navigateToReviewPage(page)

    // Verify header is visible at top
    const header = page.locator('header').first()
    await expect(header).toBeVisible()

    // Get initial position
    const initialBox = await header.boundingBox()
    expect(initialBox).toBeTruthy()

    // Scroll down the page
    await page.evaluate(() => window.scrollBy(0, 500))

    // Wait a moment for scroll to complete
    await page.waitForTimeout(500)

    // Verify header is still visible (sticky)
    await expect(header).toBeVisible()

    // Verify header position hasn't changed (should stay at top)
    const afterScrollBox = await header.boundingBox()
    expect(afterScrollBox?.y).toBe(initialBox?.y)
  })

  test('should complete full workflow: upload → process → review → approve → download', async ({ page }) => {
    // This test covers the complete end-to-end flow

    // Step 1: Navigate to create new declaration (simplified for MVP)
    await page.goto('/declarations/new')

    // Fill basic info
    await page.getByLabel(/importer.*name/i).fill('E2E Test Company')
    await page.getByLabel(/total.*value/i).fill('25000.00')

    // Save as draft
    await page.getByRole('button', { name: /save/i }).click()
    await expect(page.getByText(/saved/i)).toBeVisible()

    // Step 2: Upload documents (mocked for E2E)
    // In real scenario, would use uploadMultipleFiles helper
    // For this test, we assume documents are already uploaded

    // Step 3: Navigate to review page
    await page.goto('/declarations')
    await page.getByRole('button', { name: /review/i }).first().click()

    // Wait for review page to load
    await expect(page.getByRole('heading', { name: /review/i })).toBeVisible()

    // Step 4: Make edits if needed (triggers auto-save)
    await page.getByLabel(/importer.*name/i).first().fill('E2E Test Company Updated')
    await waitForAutoSaveComplete(page)

    // Step 5: Approve declaration
    const approveButton = page.getByRole('button', { name: /approve/i })
    await approveButton.click()
    await expect(page.getByText(/approved successfully/i)).toBeVisible()

    // Step 6: Download Excel
    const downloadButton = page.getByRole('button', { name: /download.*excel/i })
    const downloadPromise = page.waitForEvent('download')
    await downloadButton.click()

    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/CD_.*\.xlsx$/i)
    expect(await download.failure()).toBeNull()

    // Verify final success message
    await expect(page.getByText(/approved and exported successfully/i)).toBeVisible()
  })
})
