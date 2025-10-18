/**
 * Login helper for E2E tests
 */

import { Page } from '@playwright/test'

export interface LoginCredentials {
  email: string
  password: string
}

/**
 * Navigate to login page and perform login
 */
export async function login(page: Page, credentials: LoginCredentials) {
  // Navigate to login page
  await page.goto('/login')

  // Fill in credentials
  await page.getByLabel(/email/i).fill(credentials.email)
  await page.getByLabel(/password/i).fill(credentials.password)

  // Submit form
  await page.getByRole('button', { name: /log in|sign in/i }).click()

  // Wait for navigation to complete (e.g., redirect to dashboard)
  await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 })
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
