'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useHealth } from '@/hooks/use-health'
import { useAuth, useLogout } from '@/hooks/use-auth'

export function Header() {
  const pathname = usePathname()
  const { data: health, isError } = useHealth()
  const { user, isAuthenticated } = useAuth()
  const logoutMutation = useLogout()

  const navItems = [
    { href: '/declarations', label: 'Declarations' },
    { href: '/upload', label: 'Upload' },
  ]

  const handleLogout = () => {
    logoutMutation.mutate()
  }

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!user) return 'U'
    const names = user.full_name.split(' ')
    if (names.length >= 2) {
      return `${names[0][0]}${names[1][0]}`.toUpperCase()
    }
    return user.full_name[0].toUpperCase()
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white shadow-sm">
      <div className="container mx-auto flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-slate-700">
              Customs Declaration Platform
            </h1>
          </Link>
          <nav className="flex items-center gap-6">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'text-sm font-medium transition-colors hover:text-slate-700',
                  pathname === item.href
                    ? 'text-slate-700'
                    : 'text-slate-500'
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <Badge
            variant={health?.status === 'healthy' ? 'default' : 'destructive'}
          >
            API: {isError ? 'Offline' : health?.status || 'Loading...'}
          </Badge>

          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-slate-200 flex items-center justify-center">
                  <span className="text-sm font-medium text-slate-700">
                    {getUserInitials()}
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{user.full_name}</span>
                  <span className="text-xs text-slate-500 capitalize">{user.role}</span>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                disabled={logoutMutation.isPending}
              >
                {logoutMutation.isPending ? 'Logging out...' : 'Logout'}
              </Button>
            </div>
          ) : (
            <Link href="/login">
              <Button variant="ghost" size="sm">
                Login
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
