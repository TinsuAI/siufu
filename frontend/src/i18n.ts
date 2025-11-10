import { getRequestConfig } from 'next-intl/server'
import { notFound } from 'next/navigation'

// Supported locales for the application
export const locales = ['en', 'vi'] as const
export type Locale = (typeof locales)[number]

// Default locale
export const defaultLocale: Locale = 'en'

export default getRequestConfig(async ({ requestLocale }) => {
  // Get the locale from the request
  const locale = (await requestLocale) || defaultLocale

  // Validate that the incoming locale parameter is valid
  if (!locales.includes(locale as Locale)) {
    notFound()
  }

  // Load all message namespaces for the locale
  const [common, auth] = await Promise.all([
    import(`../messages/${locale}/common.json`).then(
      (module) => module.default
    ),
    import(`../messages/${locale}/auth.json`).then((module) => module.default),
  ])

  return {
    locale,
    messages: {
      common,
      auth,
    },
  }
})
