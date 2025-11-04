/**
 * Helper to create test declarations for E2E testing
 *
 * Uploads sample files from resources/sample/ and processes them
 * to create declarations in READY_FOR_REVIEW status for testing
 */

import { Page, expect } from '@playwright/test'
import path from 'path'

/**
 * Upload sample declaration files and wait for processing to complete
 * Returns the declaration ID
 */
export async function createTestDeclaration(
  page: Page,
  sampleNumber: number = 1
): Promise<string> {
  const sampleDir = path.join(process.cwd(), 'resources', 'sample', sampleNumber.toString())

  // Navigate to upload/new declaration page
  await page.goto('/declarations/new')

  // Upload required files
  const files = [
    { name: 'INVOICE.jpg', selector: 'invoice' },
    { name: 'BOL.pdf', selector: 'bill-of-lading' },
    { name: 'CO.pdf', selector: 'certificate-of-origin' },
    { name: 'AN.pdf', selector: 'packing-list' }
  ]

  for (const file of files) {
    const filePath = path.join(sampleDir, file.name)
    const fileInput = page.locator(`input[type="file"][data-testid="${file.selector}"]`)

    if (await fileInput.isVisible().catch(() => false)) {
      await fileInput.setInputFiles(filePath)
    } else {
      // Fallback: look for general file upload
      const generalInput = page.locator('input[type="file"]').first()
      await generalInput.setInputFiles(filePath)
    }
  }

  // Wait for upload completion
  await expect(page.getByText(/upload.*complete|files.*uploaded/i)).toBeVisible({ timeout: 30000 })

  // Start processing
  const processButton = page.getByRole('button', { name: /process|start.*processing/i })
  if (await processButton.isVisible().catch(() => false)) {
    await processButton.click()
  }

  // Wait for processing to complete (AI processing may take time)
  await expect(
    page.getByText(/processing.*complete|ready.*for.*review/i)
  ).toBeVisible({ timeout: 120000 }) // 2 minutes for AI processing

  // Extract declaration ID from URL or page
  await page.waitForURL(/\/declarations\/[^/]+/, { timeout: 10000 })
  const url = page.url()
  const declarationId = url.match(/\/declarations\/([^/]+)/)?.[1]

  if (!declarationId) {
    throw new Error('Could not extract declaration ID from URL')
  }

  return declarationId
}

/**
 * Simpler version: Create declaration via API calls instead of UI
 * This is faster and more reliable for E2E test setup
 */
export async function createTestDeclarationViaAPI(
  page: Page,
  sampleNumber: number = 1
): Promise<string> {
  const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'
  const sampleDir = path.join(process.cwd(), 'resources', 'sample', sampleNumber.toString())

  // Get auth token from cookies (assumes user is already logged in)
  const cookies = await page.context().cookies()
  const authCookie = cookies.find(c => c.name === 'access_token' || c.name === 'token')

  // Create declaration
  const createResponse = await page.request.post(`${apiURL}/api/v1/declarations`, {
    headers: authCookie ? { 'Cookie': `${authCookie.name}=${authCookie.value}` } : {},
    data: {
      importer_name: 'E2E Test Company',
      importer_address: '123 Test Street',
      total_value: 10000.00,
      currency: 'USD'
    }
  })

  if (!createResponse.ok()) {
    throw new Error(`Failed to create declaration: ${createResponse.status()}`)
  }

  const declaration = await createResponse.json()
  const declarationId = declaration.id

  // Upload files
  const files = ['INVOICE.jpg', 'BOL.pdf', 'CO.pdf', 'AN.pdf']

  for (const fileName of files) {
    const filePath = path.join(sampleDir, fileName)
    const fileBuffer = require('fs').readFileSync(filePath)

    await page.request.post(`${apiURL}/api/v1/declarations/${declarationId}/upload`, {
      headers: authCookie ? { 'Cookie': `${authCookie.name}=${authCookie.value}` } : {},
      multipart: {
        file: {
          name: fileName,
          mimeType: fileName.endsWith('.pdf') ? 'application/pdf' : 'image/jpeg',
          buffer: fileBuffer
        }
      }
    })
  }

  // Trigger processing
  await page.request.post(`${apiURL}/api/v1/declarations/${declarationId}/process`, {
    headers: authCookie ? { 'Cookie': `${authCookie.name}=${authCookie.value}` } : {}
  })

  // Poll for processing completion
  let attempts = 0
  const maxAttempts = 60 // 60 * 2 = 120 seconds max

  while (attempts < maxAttempts) {
    const statusResponse = await page.request.get(`${apiURL}/api/v1/declarations/${declarationId}`, {
      headers: authCookie ? { 'Cookie': `${authCookie.name}=${authCookie.value}` } : {}
    })

    if (statusResponse.ok()) {
      const status = await statusResponse.json()
      if (status.status === 'READY_FOR_REVIEW') {
        return declarationId
      }
      if (status.status === 'FAILED') {
        throw new Error(`Declaration processing failed: ${status.processing_error}`)
      }
    }

    await page.waitForTimeout(2000) // Wait 2 seconds before next poll
    attempts++
  }

  throw new Error('Declaration processing timed out')
}

/**
 * Navigate directly to a declaration's review page
 */
export async function navigateToReview(page: Page, declarationId: string) {
  await page.goto(`/declarations/${declarationId}/review`)
  await expect(page.getByRole('heading', { name: /review/i })).toBeVisible({ timeout: 10000 })
}
