/**
 * E2E Happy Path Test
 *
 * Tests the complete declaration workflow:
 * Login → Upload Files → Process → Review → Approve → Download
 */

import { test, expect } from '@playwright/test'
import { login } from './helpers/login'
import { uploadMultipleFiles, waitForFileProcessing } from './helpers/file-upload'

test.describe('Declaration Happy Path', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await login(page, {
      email: 'test@example.com',
      password: 'testpassword123'
    })
  })

  test('should complete full declaration workflow', async ({ page }) => {
    // Step 1: Navigate to create new declaration
    await page.goto('/declarations/new')
    await expect(page).toHaveTitle(/new declaration|create declaration/i)

    // Step 2: Fill in basic declaration information
    await page.getByLabel(/importer name/i).fill('ABC Import Corp')
    await page.getByLabel(/importer address/i).fill('123 Business Street, City, Country')
    await page.getByLabel(/total value/i).fill('10500.50')
    await page.getByLabel(/currency/i).selectOption('USD')

    // Save declaration as draft
    await page.getByRole('button', { name: /save.*draft/i }).click()

    // Wait for success message
    await expect(page.getByText(/declaration.*saved/i)).toBeVisible()

    // Get the declaration number for later reference
    const declarationNumber = await page.locator('[data-testid="declaration-number"]').textContent()
    expect(declarationNumber).toMatch(/DECL-\d{4}-\d{3}/)

    // Step 3: Upload required documents
    await page.getByRole('button', { name: /upload.*documents/i }).click()

    // Upload all 6 required files
    const requiredFiles = [
      'invoice.pdf',
      'bill-of-lading.pdf',
      'certificate-of-origin.pdf',
      'packing-list.xlsx',
      'goods-list.xlsx',
      'tariff-classification.xlsx'
    ]

    for (const fileName of requiredFiles) {
      await uploadMultipleFiles(page, [fileName], {
        waitForCompletion: true,
        timeout: 30000
      })
    }

    // Verify all files uploaded successfully
    for (const fileName of requiredFiles) {
      await expect(page.getByText(new RegExp(fileName, 'i'))).toBeVisible()
      await expect(page.getByText(new RegExp(`${fileName}.*uploaded`, 'i'))).toBeVisible()
    }

    // Step 4: Process documents with AI
    await page.getByRole('button', { name: /process.*documents|start.*processing/i }).click()

    // Wait for processing to complete (this may take a while)
    await expect(page.getByText(/processing.*complete|documents.*processed/i)).toBeVisible({
      timeout: 120000  // 2 minutes for AI processing
    })

    // Step 5: Review extracted data
    await page.getByRole('button', { name: /review.*data|view.*results/i }).click()

    // Verify key data fields were extracted
    await expect(page.getByText(/invoice number/i)).toBeVisible()
    await expect(page.getByText(/total.*amount/i)).toBeVisible()
    await expect(page.getByText(/hs.*code|tariff.*code/i)).toBeVisible()

    // Check for any validation warnings
    const hasWarnings = await page.getByText(/warning|attention/i).isVisible()
    if (hasWarnings) {
      console.log('Warnings detected - reviewing')
      // In production, might need to resolve warnings here
    }

    // Step 6: Approve and submit declaration
    await page.getByRole('button', { name: /approve|submit.*declaration/i }).click()

    // Confirm submission in modal/dialog
    await page.getByRole('button', { name: /confirm|yes/i }).click()

    // Wait for submission success
    await expect(page.getByText(/declaration.*submitted|submission.*successful/i)).toBeVisible({
      timeout: 30000
    })

    // Verify status changed to "submitted"
    const status = await page.locator('[data-testid="declaration-status"]').textContent()
    expect(status?.toLowerCase()).toContain('submitted')

    // Step 7: Download generated declaration
    await page.getByRole('button', { name: /download|export/i }).click()

    // Wait for download to start
    const downloadPromise = page.waitForEvent('download')
    await page.getByRole('menuitem', { name: /pdf|declaration.*pdf/i }).click()

    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/\.pdf$/i)

    // Verify download completed successfully
    expect(await download.failure()).toBeNull()
  })

  test('should allow saving declaration as draft and resuming later', async ({ page }) => {
    // Create draft declaration
    await page.goto('/declarations/new')

    await page.getByLabel(/importer name/i).fill('XYZ Trading Ltd')
    await page.getByLabel(/importer address/i).fill('456 Commerce Ave')
    await page.getByLabel(/total value/i).fill('5000')
    await page.getByLabel(/currency/i).selectOption('EUR')

    await page.getByRole('button', { name: /save.*draft/i }).click()
    await expect(page.getByText(/declaration.*saved/i)).toBeVisible()

    const declarationNumber = await page.locator('[data-testid="declaration-number"]').textContent()

    // Navigate away
    await page.goto('/declarations')

    // Find and resume the draft
    await page.getByRole('link', { name: new RegExp(declarationNumber!, 'i') }).click()

    // Verify we can edit the draft
    await expect(page.getByLabel(/importer name/i)).toHaveValue('XYZ Trading Ltd')
    await expect(page.locator('[data-testid="declaration-status"]')).toHaveText(/draft/i)

    // Can continue editing
    await page.getByLabel(/importer name/i).fill('XYZ Trading Ltd - Updated')
    await page.getByRole('button', { name: /save/i }).click()
    await expect(page.getByText(/saved/i)).toBeVisible()
  })
})
