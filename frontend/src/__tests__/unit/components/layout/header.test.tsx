import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Header } from '@/components/layout/header'

// Mock next-intl navigation (used by header)
vi.mock('@/navigation', () => ({
  Link: ({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode
    href: string
    [key: string]: unknown
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
  usePathname: () => '/declarations',
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
    back: vi.fn(),
    prefetch: vi.fn(),
  }),
}))

// Mock next/navigation for params
vi.mock('next/navigation', () => ({
  useParams: () => ({ locale: 'en' }),
}))

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

    expect(screen.getByText('Siufu')).toBeInTheDocument()
    // Translations return from the mock - check case-insensitively
    expect(screen.getByText(/declarations/i)).toBeInTheDocument()
    expect(screen.getByText(/upload/i)).toBeInTheDocument()
  })

  it('should render user menu with profile details and logout action', () => {
    renderHeader()

    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByText(/admin/i)).toBeInTheDocument()
    // Translation returns 'Logout'
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
