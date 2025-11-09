/**
 * Vitest global test setup
 *
 * This file configures the test environment for all tests.
 */

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Reset handlers after each test (important for test isolation)
afterEach(() => {
  cleanup()
})

// Mock Next.js router at global level
global.matchMedia =
  global.matchMedia ||
  function () {
    return {
      matches: false,
      addListener: function () {},
      removeListener: function () {},
    }
  }

// Mock URL.createObjectURL and URL.revokeObjectURL for PDF viewer tests
global.URL.createObjectURL = () => 'blob:mock-url'
global.URL.revokeObjectURL = () => {}

// Mock hasPointerCapture for Radix UI components (not supported in jsdom)
if (typeof Element !== 'undefined') {
  Element.prototype.hasPointerCapture =
    Element.prototype.hasPointerCapture ||
    function () {
      return false
    }
  Element.prototype.setPointerCapture =
    Element.prototype.setPointerCapture || function () {}
  Element.prototype.releasePointerCapture =
    Element.prototype.releasePointerCapture || function () {}
  Element.prototype.scrollIntoView =
    Element.prototype.scrollIntoView || function () {}
}
