/**
 * Global Setup for E2E Tests
 *
 * Runs once before all tests to:
 * - Verify services are running
 * - Create test user if needed
 * - Seed test data (declarations in various statuses)
 */

import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  const baseURL = config.use?.baseURL || 'http://localhost:8779'
  const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'

  console.log(`\n🔧 Global Setup: Verifying services...`)
  console.log(`   Frontend: ${baseURL}`)
  console.log(`   Backend API: ${apiURL}`)

  const browser = await chromium.launch()
  const page = await browser.newPage()

  try {
    // Check frontend is accessible
    const frontendResponse = await page.goto(baseURL)
    if (!frontendResponse || frontendResponse.status() >= 400) {
      throw new Error(`Frontend not accessible at ${baseURL}`)
    }
    console.log(`   ✓ Frontend is accessible`)

    // Check backend API is accessible
    const apiResponse = await page.request.get(`${apiURL}/health`)
    if (apiResponse.status() >= 400) {
      throw new Error(`Backend API not accessible at ${apiURL}/health`)
    }
    console.log(`   ✓ Backend API is accessible`)

    // TODO: Seed test data via API
    // For now, tests will need to work with existing data or skip if no data available
    console.log(`\n⚠️  Note: E2E tests require declarations in READY_FOR_REVIEW status`)
    console.log(`   Tests may be skipped if test data is not available\n`)

  } catch (error) {
    console.error(`\n❌ Global Setup Failed:`, error)
    console.error(`\nPlease ensure services are running:`)
    console.error(`   docker compose up -d\n`)
    throw error
  } finally {
    await browser.close()
  }
}

export default globalSetup
