/**
 * Login helper for E2E tests
 */

import { Page } from '@playwright/test'

export interface LoginCredentials {
  email: string
  password: string
}

/**
 * Navigate to login page and perform login via UI form
 */
export async function login(page: Page, credentials: LoginCredentials) {
  // Navigate to login page
  await page.goto('/login')

  // Fill in credentials
  await page.getByLabel(/email/i).fill(credentials.email)
  await page.getByLabel(/password/i).fill(credentials.password)

  // Wait for login API response
  const loginResponsePromise = page.waitForResponse(
    response => response.url().includes('/api/v1/auth/login') && response.status() === 200,
    { timeout: 10000 }
  )

  // Submit form
  await page.getByRole('main').getByRole('button', { name: /^login$/i }).click()

  // Wait for login to complete
  const loginResponse = await loginResponsePromise

  // Verify login was successful
  if (!loginResponse.ok()) {
    const responseBody = await loginResponse.text()
    throw new Error(`Login failed: ${loginResponse.status()} - ${responseBody}`)
  }

  // Wait for logout button to appear (confirms authentication in UI)
  await page.getByRole('button', { name: /logout/i }).waitFor({ timeout: 10000 })

  // Give the app a moment to fully process authentication
  await page.waitForTimeout(500)
}

/**
 * Perform logout
 */
export async function logout(page: Page) {
  // Click user menu or logout button
  await page.getByRole('button', { name: /logout|sign out/i }).click()

  // Wait for redirect to login page
  await page.waitForURL(/\/login/, { timeout: 5000 })
}

/**
 * Check if user is logged in by looking for common authenticated elements
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  try {
    // Look for common authenticated UI elements
    await page.getByRole('button', { name: /logout/i }).waitFor({ timeout: 2000 })
    return true
  } catch {
    return false
  }
}
