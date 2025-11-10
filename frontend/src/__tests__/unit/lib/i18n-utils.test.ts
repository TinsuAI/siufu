import { describe, it, expect } from 'vitest'
import {
  getLocalizedPath,
  getLocaleFromPathname,
  removeLocaleFromPathname,
  isValidLocale,
  getLocaleDisplayName,
  getLocaleNativeName,
} from '@/lib/i18n-utils'

describe('i18n-utils', () => {
  describe('getLocalizedPath', () => {
    it('should add locale prefix to path', () => {
      expect(getLocalizedPath('/dashboard', 'en')).toBe('/en/dashboard')
      expect(getLocalizedPath('/dashboard', 'vi')).toBe('/vi/dashboard')
    })

    it('should handle paths with leading slash', () => {
      expect(getLocalizedPath('/login', 'en')).toBe('/en/login')
    })

    it('should handle paths without leading slash', () => {
      expect(getLocalizedPath('login', 'en')).toBe('/en/login')
    })
  })

  describe('getLocaleFromPathname', () => {
    it('should extract locale from pathname', () => {
      expect(getLocaleFromPathname('/en/dashboard')).toBe('en')
      expect(getLocaleFromPathname('/vi/declarations')).toBe('vi')
    })

    it('should return default locale for invalid locale', () => {
      expect(getLocaleFromPathname('/invalid/page')).toBe('en')
      expect(getLocaleFromPathname('/dashboard')).toBe('en')
    })

    it('should handle root paths', () => {
      expect(getLocaleFromPathname('/en')).toBe('en')
      expect(getLocaleFromPathname('/vi')).toBe('vi')
    })
  })

  describe('removeLocaleFromPathname', () => {
    it('should remove locale prefix from pathname', () => {
      expect(removeLocaleFromPathname('/en/dashboard')).toBe('/dashboard')
      expect(removeLocaleFromPathname('/vi/declarations')).toBe('/declarations')
    })

    it('should return / for root locale paths', () => {
      expect(removeLocaleFromPathname('/en')).toBe('/')
      expect(removeLocaleFromPathname('/vi')).toBe('/')
    })

    it('should handle paths without locale', () => {
      expect(removeLocaleFromPathname('/dashboard')).toBe('/dashboard')
    })
  })

  describe('isValidLocale', () => {
    it('should return true for valid locales', () => {
      expect(isValidLocale('en')).toBe(true)
      expect(isValidLocale('vi')).toBe(true)
    })

    it('should return false for invalid locales', () => {
      expect(isValidLocale('fr')).toBe(false)
      expect(isValidLocale('invalid')).toBe(false)
      expect(isValidLocale('')).toBe(false)
    })
  })

  describe('getLocaleDisplayName', () => {
    it('should return display names for locales', () => {
      expect(getLocaleDisplayName('en')).toBe('English')
      expect(getLocaleDisplayName('vi')).toBe('Tiếng Việt')
    })
  })

  describe('getLocaleNativeName', () => {
    it('should return native names for locales', () => {
      expect(getLocaleNativeName('en')).toBe('EN')
      expect(getLocaleNativeName('vi')).toBe('VI')
    })
  })
})
