/**
 * Vitest global test setup
 *
 * This file configures the test environment for all tests.
 */

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Reset handlers after each test (important for test isolation)
afterEach(() => {
  cleanup();
});

// Mock Next.js router at global level
global.matchMedia =
  global.matchMedia ||
  function () {
    return {
      matches: false,
      addListener: function () {},
      removeListener: function () {},
    };
  };
