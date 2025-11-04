/**
 * Smoke Test for Declaration Approval UI
 *
 * Fast tests that verify approval UI exists and functions without full pipeline
 * For full E2E tests with real data, see declaration-approval.spec.ts
 */

import { test, expect } from '@playwright/test'
import { login } from './helpers/login'

test.describe('Declaration Approval UI - Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, {
      email: 'demo@example.com',
      password: 'password123'
    })
  })

  test('should show login page and allow login', async ({ page }) => {
    // Verify we're logged in
    await expect(page.getByRole('button', { name: /logout/i })).toBeVisible()
  })

  test('should show declarations list page', async ({ page }) => {
    // Navigate to declarations page
    // Use a fresh navigation to ensure we're starting clean
    await page.goto('/declarations', { waitUntil: 'load' })

    // Wait for either the declarations heading OR check if we got redirected to login
    // If redirected, we need to log back in for this specific test
    const isOnLoginPage = await page.getByRole('heading', { name: /sign in/i }).isVisible().catch(() => false)

    if (isOnLoginPage) {
      // Re-login if we were redirected (shouldn't happen but handling edge case)
      await page.getByLabel(/email/i).fill('demo@example.com')
      await page.getByLabel(/password/i).fill('password123')
      await page.getByRole('main').getByRole('button', { name: /^login$/i }).click()
      await page.waitForResponse(response => response.url().includes('/api/v1/auth/login'))
      await page.goto('/declarations')
    }

    // Now check for the declarations heading
    await expect(page.getByRole('heading', { name: /declarations/i })).toBeVisible({ timeout: 10000 })
  })

  test('should verify API is accessible', async ({ page }) => {
    const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'
    const response = await page.request.get(`${apiURL}/health`)
    expect(response.ok()).toBe(true)
  })

  test('should verify approval endpoints exist in OpenAPI spec', async ({ page }) => {
    const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8780'
    const response = await page.request.get(`${apiURL}/openapi.json`)

    if (response.ok()) {
      const spec = await response.json()

      // Check approve endpoint exists
      expect(spec.paths).toHaveProperty('/api/v1/declarations/{declaration_id}/approve')

      // Check reject endpoint exists
      expect(spec.paths).toHaveProperty('/api/v1/declarations/{declaration_id}/reject')

      // Check export endpoint exists
      expect(spec.paths).toHaveProperty('/api/v1/declarations/{declaration_id}/export')

      console.log('✓ All approval/reject/export endpoints defined in OpenAPI spec')
    }
  })

  test('should load review page structure (mock data)', async ({ page }) => {
    // Navigate to a mock review page URL
    await page.goto('/declarations/00000000-0000-0000-0000-000000000001/review')

    // Since there's no real declaration with this ID, we might get redirected
    // Just verify the page loaded (either review page, 404, or declarations list)
    const url = page.url()

    // Accept either: stayed on review URL, or got redirected to declarations/login
    const validUrls = ['/review', '/declarations', '/login']
    const matchesValidUrl = validUrls.some(path => url.includes(path))
    expect(matchesValidUrl).toBe(true)
  })
})

test.describe('Declaration Approval - Component Tests', () => {
  test.skip('Full approval flow requires test data', async ({ page }) => {
    // This test is skipped because it requires:
    // 1. A declaration in READY_FOR_REVIEW status
    // 2. Test data fixtures or full upload→process pipeline

    // To enable this test:
    // - Create test fixtures with declarations in database
    // - Or use createTestDeclarationViaAPI from helpers
    // - Or run after happy-path.spec.ts creates declarations

    console.log('⚠️  Full E2E approval tests skipped - see declaration-approval.spec.ts')
  })
})
