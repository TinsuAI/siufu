import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Header } from '@/components/layout/header'

// Mock next/navigation
vi.mock('next/navigation', () => {
  const push = vi.fn()
  const replace = vi.fn()
  const refresh = vi.fn()
  const back = vi.fn()

  return {
    usePathname: () => '/declarations',
    useRouter: () => ({
      push,
      replace,
      refresh,
      back,
      prefetch: vi.fn(),
    }),
  }
})

// Mock the health hook
vi.mock('@/hooks/use-health', () => ({
  useHealth: () => ({
    data: { status: 'healthy', version: '1.0.0' },
    isError: false,
  }),
}))

const mockLogout = vi.fn()

// Mock auth hooks to avoid React Query requirements in tests
vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({
    user: {
      full_name: 'Test User',
      role: 'admin',
    },
    isAuthenticated: true,
    isLoading: false,
  }),
  useLogout: () => ({
    mutate: mockLogout,
    isPending: false,
  }),
}))

describe('Header', () => {
  const renderHeader = () => {
    const queryClient = new QueryClient()
    return render(
      <QueryClientProvider client={queryClient}>
        <Header />
      </QueryClientProvider>
    )
  }

  it('should render header with navigation links', () => {
    renderHeader()

    expect(screen.getByText('Customs Declaration Platform')).toBeInTheDocument()
    expect(screen.getByText('Declarations')).toBeInTheDocument()
    expect(screen.getByText('Upload')).toBeInTheDocument()
  })

  it('should render user menu with profile details and logout action', () => {
    renderHeader()

    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByText(/admin/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument()
  })

  it('should display API health status', () => {
    renderHeader()

    expect(screen.getByText(/API:/)).toBeInTheDocument()
  })

  it('should render user avatar placeholder', () => {
    renderHeader()

    const avatar = screen.getByText('TU')
    expect(avatar).toBeInTheDocument()
  })
})
