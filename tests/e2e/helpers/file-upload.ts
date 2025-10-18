/**
 * File upload helper for E2E tests
 */

import { Page, Locator } from '@playwright/test'
import path from 'path'

export interface UploadFileOptions {
  /**
   * Selector for file input element
   */
  selector?: string
  /**
   * Wait for upload completion indicator
   */
  waitForCompletion?: boolean
  /**
   * Timeout for upload completion in ms
   */
  timeout?: number
}

/**
 * Upload a single file
 */
export async function uploadFile(
  page: Page,
  filePath: string,
  options: UploadFileOptions = {}
) {
  const {
    selector = 'input[type="file"]',
    waitForCompletion = true,
    timeout = 30000
  } = options

  // Get absolute path to test fixture
  const absolutePath = path.resolve(__dirname, '../fixtures', filePath)

  // Find file input and upload
  const fileInput = page.locator(selector)
  await fileInput.setInputFiles(absolutePath)

  if (waitForCompletion) {
    // Wait for upload success indicator
    await page.getByText(/upload.*complete|successfully uploaded/i).waitFor({
      timeout,
      state: 'visible'
    })
  }
}

/**
 * Upload multiple files
 */
export async function uploadMultipleFiles(
  page: Page,
  filePaths: string[],
  options: UploadFileOptions = {}
) {
  const {
    selector = 'input[type="file"]',
    waitForCompletion = true,
    timeout = 30000
  } = options

  // Convert to absolute paths
  const absolutePaths = filePaths.map(fp =>
    path.resolve(__dirname, '../fixtures', fp)
  )

  // Find file input and upload all files
  const fileInput = page.locator(selector)
  await fileInput.setInputFiles(absolutePaths)

  if (waitForCompletion) {
    // Wait for all uploads to complete
    for (const filePath of filePaths) {
      const fileName = path.basename(filePath)
      await page.getByText(new RegExp(fileName, 'i')).waitFor({
        timeout,
        state: 'visible'
      })
    }
  }
}

/**
 * Clear uploaded files
 */
export async function clearUploadedFiles(page: Page, selector: string = 'input[type="file"]') {
  const fileInput = page.locator(selector)
  await fileInput.setInputFiles([])
}

/**
 * Wait for file processing to complete
 */
export async function waitForFileProcessing(
  page: Page,
  fileName: string,
  timeout: number = 60000
) {
  // Wait for processing status to change from "processing" to "completed"
  await page.getByText(new RegExp(`${fileName}.*completed`, 'i')).waitFor({
    timeout,
    state: 'visible'
  })
}
