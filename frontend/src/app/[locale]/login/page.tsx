'use client'

import { useState, FormEvent } from 'react'
import { useTranslations } from 'next-intl'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useLogin } from '@/hooks/use-auth'

export default function LoginPage() {
  const t = useTranslations('auth')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const loginMutation = useLogin()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    // Basic validation
    if (!email || !password) {
      setError(t('login.errors.required'))
      return
    }

    if (password.length < 8) {
      setError(t('login.errors.passwordTooShort'))
      return
    }

    loginMutation.mutate(
      { email, password },
      {
        onError: (error: Error) => {
          setError(error.message)
        },
      }
    )
  }

  const isLoading = loginMutation.isPending

  return (
    <div className="container mx-auto flex min-h-[calc(100vh-4rem)] items-center justify-center px-6">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">
            {t('login.title')}
          </CardTitle>
          <CardDescription>{t('login.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                {t('login.emailLabel')}
              </label>
              <Input
                id="email"
                type="email"
                placeholder={t('login.emailPlaceholder')}
                autoComplete="email"
                disabled={isLoading}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                {t('login.passwordLabel')}
              </label>
              <Input
                id="password"
                type="password"
                placeholder={t('login.passwordPlaceholder')}
                autoComplete="current-password"
                disabled={isLoading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {/* Remember Me Checkbox (UI only for MVP) */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="rememberMe"
                disabled={isLoading}
                className="h-4 w-4 rounded border-gray-300"
              />
              <label
                htmlFor="rememberMe"
                className="text-sm font-normal cursor-pointer"
              >
                {t('login.rememberMe')}
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                {error}
              </div>
            )}

            {/* Login Button */}
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? t('login.loggingIn') : t('login.submitButton')}
            </Button>
          </form>

          {/* Demo Credentials Hint */}
          <div className="mt-4 text-center text-sm text-slate-600">
            <p>{t('login.demoCredentials')}</p>
            <p className="font-mono text-xs">demo@example.com / password123</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
