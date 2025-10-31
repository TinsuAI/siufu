import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Header } from '@/components/layout/header'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/declarations',
}))

// Mock the health hook
vi.mock('@/hooks/use-health', () => ({
  useHealth: () => ({
    data: { status: 'healthy', version: '1.0.0' },
    isError: false,
  }),
}))

describe('Header', () => {
  it('should render header with navigation links', () => {
    render(<Header />)

    expect(
      screen.getByText('Customs Declaration Platform')
    ).toBeInTheDocument()
    expect(screen.getByText('Declarations')).toBeInTheDocument()
    expect(screen.getByText('Upload')).toBeInTheDocument()
  })

  it('should render user menu options', () => {
    render(<Header />)

    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Logout')).toBeInTheDocument()
  })

  it('should display API health status', () => {
    render(<Header />)

    expect(screen.getByText(/API:/)).toBeInTheDocument()
  })

  it('should render user avatar placeholder', () => {
    render(<Header />)

    const avatar = screen.getByText('U')
    expect(avatar).toBeInTheDocument()
  })
})
