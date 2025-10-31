/**
 * Next.js Middleware for route protection
 * Runs on every request to check authentication status
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Protected routes that require authentication
const protectedRoutes = [
  '/declarations',
  '/upload',
  '/analytics',
  '/knowledge-base',
]

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Get the access token from cookies
  const accessToken = request.cookies.get('access_token')?.value

  // Check if the route is protected and redirect if unauthenticated
  if (protectedRoutes.some((route) => pathname.startsWith(route)) && !accessToken) {
    const loginUrl = new URL('/login', request.url)
    return NextResponse.redirect(loginUrl)
  }

  // If accessing login page with a valid token, redirect to declarations
  if (pathname === '/login' && accessToken) {
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
        const declarationsUrl = new URL('/declarations', request.url)
        return NextResponse.redirect(declarationsUrl)
      }
    } catch (error) {
      // If verification fails, allow access to login page
      void error // Suppress unused variable warning
    }
  }

  return NextResponse.next()
}

// Configure which routes the middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public directory)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
