/**
 * Vitest global test setup
 *
 * This file configures the test environment for all tests.
 */

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll } from 'vitest'
import { server } from '../mocks/server'

// Start MSW server before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' })
})

// Reset handlers after each test (important for test isolation)
afterEach(() => {
  server.resetHandlers()
  cleanup()
})

// Clean up after all tests are done
afterAll(() => {
  server.close()
})

// Mock Next.js router
global.matchMedia = global.matchMedia || function () {
  return {
    matches: false,
    addListener: function () {},
    removeListener: function () {}
  }
}
