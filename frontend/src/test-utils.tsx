/**
 * Custom render utilities for testing React components
 *
 * This file provides wrappers around React Testing Library's render
 * to automatically include providers (QueryClient, Zustand, etc.)
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Create a new QueryClient for each test to ensure isolation
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,  // Don't retry failed queries in tests
        gcTime: 0,     // Disable caching in tests (previously cacheTime)
        staleTime: 0
      },
      mutations: {
        retry: false
      }
    }
  })
}

interface AllTheProvidersProps {
  children: React.ReactNode
}

/**
 * Wrapper component that provides all necessary contexts for testing
 */
export function AllTheProviders({ children }: AllTheProvidersProps) {
  const queryClient = createTestQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

/**
 * Custom render that wraps the component with all providers
 *
 * @example
 * import { renderWithProviders } from '@/test-utils'
 *
 * test('renders component', () => {
 *   renderWithProviders(<MyComponent />)
 *   // ... assertions
 * })
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllTheProviders, ...options })
}

// Re-export everything from React Testing Library
export * from '@testing-library/react'
