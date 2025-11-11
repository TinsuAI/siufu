import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LanguageSwitcher } from '@/components/layout/language-switcher'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useParams: () => ({ locale: 'en' }),
}))

// Mock our custom navigation
vi.mock('@/navigation', () => ({
  useRouter: () => ({
    replace: vi.fn(),
  }),
  usePathname: () => '/dashboard',
}))

describe('LanguageSwitcher', () => {
  it('should render language selector', () => {
    render(<LanguageSwitcher />)

    // Check that the select trigger is rendered with aria-label
    const trigger = screen.getByRole('combobox', { name: /select language/i })
    expect(trigger).toBeInTheDocument()
  })

  it('should display current locale', () => {
    render(<LanguageSwitcher />)

    // The current value should be displayed
    const trigger = screen.getByRole('combobox')
    expect(trigger).toHaveTextContent(/EN|en/i)
  })
})
