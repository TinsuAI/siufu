/**
 * Unit tests for CompanyBadge component
 * Tests verification status badges for importers/exporters
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CompanyBadge } from '@/components/declarations/company-badge'

describe('CompanyBadge', () => {
  describe('Verified Company Badge', () => {
    it('renders "Verified Company" badge when isVerified is true', () => {
      render(<CompanyBadge isVerified={true} />)

      expect(screen.getByText('Verified Company')).toBeInTheDocument()
    })

    it('displays CheckCircle2 icon for verified companies', () => {
      const { container } = render(<CompanyBadge isVerified={true} />)

      // CheckCircle2 icon renders as SVG
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('applies green background styling for verified badge', () => {
      const { container } = render(<CompanyBadge isVerified={true} />)

      const badge = container.querySelector('[class*="bg-green-500"]')
      expect(badge).toBeInTheDocument()
    })

    it('displays declaration count when provided and greater than 0', () => {
      render(<CompanyBadge isVerified={true} declarationCount={5} />)

      expect(screen.getByText(/5 declarations/)).toBeInTheDocument()
    })

    it('displays declaration count in parentheses format', () => {
      render(<CompanyBadge isVerified={true} declarationCount={10} />)

      expect(screen.getByText('(10 declarations)')).toBeInTheDocument()
    })

    it('does not display declaration count when count is 0', () => {
      render(<CompanyBadge isVerified={true} declarationCount={0} />)

      expect(screen.queryByText(/declarations/)).not.toBeInTheDocument()
    })

    it('does not display declaration count when not provided', () => {
      render(<CompanyBadge isVerified={true} />)

      expect(screen.queryByText(/declarations/)).not.toBeInTheDocument()
    })

    it('does not display declaration count when undefined', () => {
      render(<CompanyBadge isVerified={true} declarationCount={undefined} />)

      expect(screen.queryByText(/declarations/)).not.toBeInTheDocument()
    })
  })

  describe('New/Unverified Company Badge', () => {
    it('renders "New Company - Review Required" badge when isVerified is false', () => {
      render(<CompanyBadge isVerified={false} />)

      expect(
        screen.getByText('New Company - Review Required')
      ).toBeInTheDocument()
    })

    it('displays AlertTriangle icon for unverified companies', () => {
      const { container } = render(<CompanyBadge isVerified={false} />)

      // AlertTriangle icon renders as SVG
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('applies yellow background styling for unverified badge', () => {
      const { container } = render(<CompanyBadge isVerified={false} />)

      const badge = container.querySelector('[class*="bg-yellow-500"]')
      expect(badge).toBeInTheDocument()
    })

    it('does not display declaration count for unverified companies', () => {
      render(<CompanyBadge isVerified={false} declarationCount={5} />)

      // Should not show declaration count for unverified companies
      expect(screen.queryByText(/declarations/)).not.toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles very large declaration counts', () => {
      render(<CompanyBadge isVerified={true} declarationCount={9999} />)

      expect(screen.getByText('(9999 declarations)')).toBeInTheDocument()
    })

    it('handles declaration count of 1 (singular)', () => {
      render(<CompanyBadge isVerified={true} declarationCount={1} />)

      // Note: Current implementation uses plural "declarations" for all counts
      // This test documents the current behavior
      expect(screen.getByText('(1 declarations)')).toBeInTheDocument()
    })
  })
})
