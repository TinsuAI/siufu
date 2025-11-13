/**
 * Next.js Middleware for locale routing and route protection
 * Runs on every request to handle i18n and check authentication status
 */

import createIntlMiddleware from 'next-intl/middleware'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { locales, defaultLocale, type Locale } from './i18n'

// Protected routes that require authentication (without locale prefix)
const protectedRoutes = [
  '/declarations',
  '/upload',
  '/analytics',
  '/knowledge-base',
  '/companies',
]

// Create the internationalization middleware
const intlMiddleware = createIntlMiddleware({
  locales,
  defaultLocale,
  localePrefix: 'always',
  localeDetection: true,
})

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // First, handle locale routing with next-intl
  const intlResponse = intlMiddleware(request)

  // Extract locale from pathname (e.g., /en/declarations -> en)
  const pathnameLocale = pathname.split('/')[1]
  const isValidLocale = locales.includes(pathnameLocale as Locale)

  // Get the path without locale prefix for auth checks
  const pathnameWithoutLocale = isValidLocale
    ? pathname.slice(pathnameLocale.length + 1) || '/'
    : pathname

  // Get the access token from cookies
  const accessToken = request.cookies.get('access_token')?.value

  // Determine the current locale for redirects
  const currentLocale = isValidLocale ? pathnameLocale : defaultLocale

  const isProtectedRoute = protectedRoutes.some((route) =>
    pathnameWithoutLocale.startsWith(route)
  )
  const isLoginPage = pathnameWithoutLocale === '/login'

  // If accessing a protected route without a token, redirect to login
  if (isProtectedRoute && !accessToken) {
    const loginUrl = new URL(`/${currentLocale}/login`, request.url)
    return NextResponse.redirect(loginUrl)
  }

  // If accessing login page with a token, verify it and redirect to declarations if valid
  if (isLoginPage && accessToken) {
    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000/api/v1'
      const response = await fetch(`${apiUrl}/auth/me`, {
        headers: {
          Cookie: `access_token=${accessToken}`,
        },
        // Add timeout to avoid hanging
        signal: AbortSignal.timeout(3000),
      })

      // If token is valid, redirect to declarations
      if (response.ok) {
        const declarationsUrl = new URL(
          `/${currentLocale}/declarations`,
          request.url
        )
        return NextResponse.redirect(declarationsUrl)
      } else {
        // Token is invalid - clear it and allow access to login page
        const response = intlResponse || NextResponse.next()
        response.cookies.delete('access_token')
        return response
      }
    } catch (error) {
      // If verification fails (network error, timeout, etc.), clear invalid token
      void error // Suppress unused variable warning
      const response = intlResponse || NextResponse.next()
      response.cookies.delete('access_token')
      return response
    }
  }

  // If accessing a protected route with a token, let it through
  // (the client-side will handle token validation)
  if (isProtectedRoute && accessToken) {
    return intlResponse
  }

  return intlResponse
}

// Configure which routes the middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api routes
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, other static assets
     * - files with extensions (images, fonts, etc.)
     */
    '/((?!api|_next|_vercel|.*\\..*).*)',
  ],
}
