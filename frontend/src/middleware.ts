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

  // Check if the route is protected and redirect if unauthenticated
  if (
    protectedRoutes.some((route) => pathnameWithoutLocale.startsWith(route)) &&
    !accessToken
  ) {
    const loginUrl = new URL(`/${currentLocale}/login`, request.url)
    return NextResponse.redirect(loginUrl)
  }

  // If accessing login page with a valid token, redirect to declarations
  if (pathnameWithoutLocale === '/login' && accessToken) {
    // Verify the token is valid by calling the backend
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'
      const response = await fetch(`${apiUrl}/api/auth/me`, {
        headers: {
          Cookie: `access_token=${accessToken}`,
        },
      })

      // If token is valid, redirect to declarations
      if (response.ok) {
        const declarationsUrl = new URL(
          `/${currentLocale}/declarations`,
          request.url
        )
        return NextResponse.redirect(declarationsUrl)
      }
    } catch (error) {
      // If verification fails, allow access to login page
      void error // Suppress unused variable warning
    }
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
