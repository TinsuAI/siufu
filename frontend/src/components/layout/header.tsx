'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useHealth } from '@/hooks/use-health'

export function Header() {
  const pathname = usePathname()
  const { data: health, isError } = useHealth()

  const navItems = [
    { href: '/declarations', label: 'Declarations' },
    { href: '/upload', label: 'Upload' },
  ]

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
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-slate-200 flex items-center justify-center">
              <span className="text-sm font-medium text-slate-700">U</span>
            </div>
            <Button variant="ghost" size="sm">
              Profile
            </Button>
          </div>
          <Button variant="ghost" size="sm">
            Logout
          </Button>
        </div>
      </div>
    </header>
  )
}
