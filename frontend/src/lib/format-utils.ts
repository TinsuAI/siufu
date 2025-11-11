/**
 * Formatting utilities for Vietnamese and English locales
 * Story 4.3: Vietnamese date, number, and currency formatting
 */

import { useFormatter } from 'next-intl'

/**
 * Hook for formatting dates, numbers, and currency with locale support
 * @returns Formatting functions for current locale
 */
export function useFormatting() {
  const format = useFormatter()

  /**
   * Format a date according to locale conventions
   * Vietnamese: dd/MM/yyyy (e.g., 10/11/2025)
   * English: MM/dd/yyyy (e.g., 11/10/2025)
   */
  const formatDate = (date: Date | string | null | undefined): string => {
    if (!date) return ''
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return format.dateTime(dateObj, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  /**
   * Format a date with time according to locale conventions
   * Vietnamese: dd/MM/yyyy HH:mm
   * English: MM/dd/yyyy HH:mm
   */
  const formatDateTime = (date: Date | string | null | undefined): string => {
    if (!date) return ''
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return format.dateTime(dateObj, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  }

  /**
   * Format a number according to locale conventions
   * Vietnamese: 1.234.567,89 (period for thousands, comma for decimal)
   * English: 1,234,567.89 (comma for thousands, period for decimal)
   */
  const formatNumber = (
    value: number | null | undefined,
    decimals: number = 2
  ): string => {
    if (value === null || value === undefined) return ''
    return format.number(value, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  /**
   * Format currency according to locale and currency type
   * Vietnamese VND: 1.234.567 ₫ or 1.234.567 VND
   * Vietnamese USD: 1.234,56 USD
   * English VND: ₫1,234,567 or VND 1,234,567
   * English USD: $1,234.56
   */
  const formatCurrency = (
    amount: number | null | undefined,
    currency: string = 'VND'
  ): string => {
    if (amount === null || amount === undefined) return ''
    return format.number(amount, {
      style: 'currency',
      currency: currency,
    })
  }

  /**
   * Format integer without decimals
   * Vietnamese: 1.234.567
   * English: 1,234,567
   */
  const formatInteger = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return ''
    return format.number(value, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })
  }

  return {
    formatDate,
    formatDateTime,
    formatNumber,
    formatCurrency,
    formatInteger,
  }
}
