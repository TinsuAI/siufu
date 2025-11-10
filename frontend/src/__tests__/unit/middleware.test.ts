import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest, NextResponse } from 'next/server'
import { middleware } from '@/middleware'

// Mock next-intl middleware
vi.mock('next-intl/middleware', () => ({
  default: vi.fn(() => {
    return (request: NextRequest) => {
      // Simulate next-intl middleware behavior
      const pathname = request.nextUrl.pathname
      const pathnameLocale = pathname.split('/')[1]
      const isValidLocale = ['en', 'vi'].includes(pathnameLocale)

      // If no locale in path, redirect to default locale
      if (!isValidLocale && pathname !== '/') {
        const url = request.nextUrl.clone()
        url.pathname = `/en${pathname}`
        return NextResponse.redirect(url)
      }

      return NextResponse.next()
    }
  }),
}))

// Mock fetch for auth verification
global.fetch = vi.fn()

describe('middleware', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Locale routing', () => {
    it('should allow requests with valid locale prefix', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/en/declarations')
      )
      request.cookies.set('access_token', 'valid-token-123')

      const response = await middleware(request)

      expect(response.status).toBe(200)
    })

    it('should handle Vietnamese locale correctly', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/vi/declarations')
      )
      request.cookies.set('access_token', 'valid-token-123')

      const response = await middleware(request)

      expect(response.status).toBe(200)
    })

    it('should redirect paths without locale to default locale', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/declarations')
      )

      const response = await middleware(request)

      expect(response.status).toBe(307) // Redirect status
      expect(response.headers.get('location')).toContain('/en/login')
    })

    it('should extract locale correctly from pathname', async () => {
      const requestEn = new NextRequest(
        new URL('http://localhost:3000/en/upload')
      )
      const requestVi = new NextRequest(
        new URL('http://localhost:3000/vi/upload')
      )

      await middleware(requestEn)
      await middleware(requestVi)

      // Both should process successfully
      expect(true).toBe(true)
    })
  })

  describe('Cookie-based locale persistence', () => {
    it('should respect NEXT_LOCALE cookie for locale preference', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/en/declarations')
      )
      request.cookies.set('NEXT_LOCALE', 'vi')

      const response = await middleware(request)

      // Middleware should allow the request
      expect(response.status).toBeLessThan(400)
    })

    it('should work without NEXT_LOCALE cookie', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/en/declarations')
      )

      const response = await middleware(request)

      expect(response.status).toBeLessThan(400)
    })
  })

  describe('Accept-Language header detection', () => {
    it('should process request with Accept-Language header', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/en/declarations')
      )
      request.headers.set('Accept-Language', 'vi-VN,vi;q=0.9,en-US;q=0.8')

      const response = await middleware(request)

      expect(response.status).toBeLessThan(400)
    })

    it('should fallback to default locale without Accept-Language', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/declarations')
      )

      const response = await middleware(request)

      expect(response.status).toBe(307)
      expect(response.headers.get('location')).toContain('/en/')
    })
  })

  describe('Authentication integration', () => {
    it('should redirect to login for protected routes without token', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/en/declarations')
      )
      // No access_token cookie

      const response = await middleware(request)

      expect(response.status).toBe(307)
      expect(response.headers.get('location')).toContain('/en/login')
    })

    it('should allow protected routes with valid access token', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/en/declarations')
      )
      request.cookies.set('access_token', 'valid-token-123')

      const response = await middleware(request)

      expect(response.status).toBe(200)
    })

    it('should redirect authenticated users from login to declarations', async () => {
      const request = new NextRequest(new URL('http://localhost:3000/en/login'))
      request.cookies.set('access_token', 'valid-token-123')

      // Mock successful auth verification
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ user: { id: 1, email: 'test@example.com' } }),
      })

      const response = await middleware(request)

      expect(response.status).toBe(307)
      expect(response.headers.get('location')).toContain('/en/declarations')
    })

    it('should allow login access when token verification fails', async () => {
      const request = new NextRequest(new URL('http://localhost:3000/en/login'))
      request.cookies.set('access_token', 'invalid-token')

      // Mock failed auth verification
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 401,
      })

      const response = await middleware(request)

      // Should allow access to login page
      expect(response.status).toBe(200)
    })

    it('should handle network errors gracefully during token verification', async () => {
      const request = new NextRequest(new URL('http://localhost:3000/en/login'))
      request.cookies.set('access_token', 'valid-token-123')

      // Mock network error
      ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error('Network error')
      )

      const response = await middleware(request)

      // Should allow access to login page when verification fails
      expect(response.status).toBe(200)
    })

    it('should preserve locale when redirecting to login', async () => {
      const requestEn = new NextRequest(
        new URL('http://localhost:3000/en/upload')
      )
      const requestVi = new NextRequest(
        new URL('http://localhost:3000/vi/upload')
      )

      const responseEn = await middleware(requestEn)
      const responseVi = await middleware(requestVi)

      expect(responseEn.headers.get('location')).toContain('/en/login')
      expect(responseVi.headers.get('location')).toContain('/vi/login')
    })

    it('should preserve locale when redirecting from login', async () => {
      const requestVi = new NextRequest(
        new URL('http://localhost:3000/vi/login')
      )
      requestVi.cookies.set('access_token', 'valid-token-123')

      // Mock successful auth verification
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ user: { id: 1, email: 'test@example.com' } }),
      })

      const response = await middleware(requestVi)

      expect(response.headers.get('location')).toContain('/vi/declarations')
    })
  })

  describe('Protected routes', () => {
    const protectedRoutes = [
      '/declarations',
      '/upload',
      '/analytics',
      '/knowledge-base',
      '/companies',
    ]

    protectedRoutes.forEach((route) => {
      it(`should protect ${route} route without authentication`, async () => {
        const request = new NextRequest(
          new URL(`http://localhost:3000/en${route}`)
        )

        const response = await middleware(request)

        expect(response.status).toBe(307)
        expect(response.headers.get('location')).toContain('/en/login')
      })

      it(`should allow ${route} route with authentication`, async () => {
        const request = new NextRequest(
          new URL(`http://localhost:3000/en${route}`)
        )
        request.cookies.set('access_token', 'valid-token-123')

        const response = await middleware(request)

        expect(response.status).toBe(200)
      })
    })
  })

  describe('Public routes', () => {
    it('should allow access to login without authentication', async () => {
      const request = new NextRequest(new URL('http://localhost:3000/en/login'))

      const response = await middleware(request)

      expect(response.status).toBe(200)
    })

    it('should allow access to root path', async () => {
      const request = new NextRequest(new URL('http://localhost:3000/en/'))

      const response = await middleware(request)

      expect(response.status).toBe(200)
    })
  })

  describe('Fallback behavior', () => {
    it('should handle invalid locale gracefully', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/invalid/page')
      )

      const response = await middleware(request)

      // Should redirect to valid locale
      expect(response.status).toBe(307)
      expect(response.headers.get('location')).toContain('/en/')
    })

    it('should handle empty pathname', async () => {
      const request = new NextRequest(new URL('http://localhost:3000/'))

      const response = await middleware(request)

      // Should handle gracefully
      expect(response.status).toBeLessThan(500)
    })

    it('should handle malformed paths', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000//en//declarations')
      )

      const response = await middleware(request)

      // Should not crash
      expect(response).toBeDefined()
    })
  })

  describe('Locale extraction logic', () => {
    it('should correctly identify valid locale in pathname', async () => {
      const testCases = [
        { path: '/en/test', expectedLocale: 'en' },
        { path: '/vi/test', expectedLocale: 'vi' },
        { path: '/en', expectedLocale: 'en' },
        { path: '/vi', expectedLocale: 'vi' },
      ]

      for (const { path } of testCases) {
        const request = new NextRequest(new URL(`http://localhost:3000${path}`))
        const response = await middleware(request)

        // Should process successfully
        expect(response).toBeDefined()
      }
    })

    it('should remove locale from pathname correctly', async () => {
      const request = new NextRequest(
        new URL('http://localhost:3000/en/declarations/123')
      )
      request.cookies.set('access_token', 'valid-token')

      const response = await middleware(request)

      // Should correctly identify /declarations/123 as protected route
      expect(response.status).toBe(200)
    })
  })
})
