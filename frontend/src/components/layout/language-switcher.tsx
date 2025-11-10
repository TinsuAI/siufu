'use client'

import { useParams } from 'next/navigation'
import { useRouter, usePathname } from '@/navigation'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { locales, type Locale } from '@/i18n'

// Language display names
const languageNames: Record<Locale, string> = {
  en: 'EN',
  vi: 'VI',
}

export function LanguageSwitcher() {
  const params = useParams()
  const router = useRouter()
  const pathname = usePathname()

  const currentLocale = (params.locale as Locale) || 'en'

  const handleLocaleChange = (newLocale: string) => {
    // Navigate to the same path but with the new locale
    router.replace(pathname, { locale: newLocale as Locale })
  }

  return (
    <Select value={currentLocale} onValueChange={handleLocaleChange}>
      <SelectTrigger
        className="w-[80px] border-border/40 bg-background/50 hover:bg-background/80 transition-colors"
        aria-label="Select language"
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {locales.map((locale) => (
          <SelectItem key={locale} value={locale}>
            {languageNames[locale]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
