import { locales, defaultLocale, type Locale } from '@/i18n'

/**
 * Utility functions for internationalization
 */

/**
 * Get a localized path for a given route and locale
 * @param path - The route path without locale prefix
 * @param locale - The target locale
 * @returns The path with locale prefix (e.g., /en/dashboard)
 */
export function getLocalizedPath(path: string, locale: Locale): string {
  // Remove leading slash if present
  const cleanPath = path.startsWith('/') ? path.slice(1) : path

  // Add locale prefix
  return `/${locale}/${cleanPath}`
}

/**
 * Extract locale from a pathname
 * @param pathname - The full pathname (e.g., /en/dashboard)
 * @returns The extracted locale or default locale
 */
export function getLocaleFromPathname(pathname: string): Locale {
  const segments = pathname.split('/').filter(Boolean)
  const potentialLocale = segments[0]

  if (locales.includes(potentialLocale as Locale)) {
    return potentialLocale as Locale
  }

  return defaultLocale
}

/**
 * Remove locale prefix from pathname
 * @param pathname - The full pathname (e.g., /en/dashboard)
 * @returns The pathname without locale prefix (e.g., /dashboard)
 */
export function removeLocaleFromPathname(pathname: string): string {
  const locale = getLocaleFromPathname(pathname)
  const localePrefix = `/${locale}`

  if (pathname.startsWith(localePrefix)) {
    return pathname.slice(localePrefix.length) || '/'
  }

  return pathname
}

/**
 * Check if a locale is valid
 * @param locale - The locale to check
 * @returns True if the locale is supported
 */
export function isValidLocale(locale: string): locale is Locale {
  return locales.includes(locale as Locale)
}

/**
 * Get the display name for a locale
 * @param locale - The locale
 * @returns The display name (e.g., 'English', 'Tiếng Việt')
 */
export function getLocaleDisplayName(locale: Locale): string {
  const displayNames: Record<Locale, string> = {
    en: 'English',
    vi: 'Tiếng Việt',
  }

  return displayNames[locale] || locale
}

/**
 * Get the native name for a locale
 * @param locale - The locale
 * @returns The native name (e.g., 'EN', 'VI')
 */
export function getLocaleNativeName(locale: Locale): string {
  const nativeNames: Record<Locale, string> = {
    en: 'EN',
    vi: 'VI',
  }

  return nativeNames[locale] || locale.toUpperCase()
}
