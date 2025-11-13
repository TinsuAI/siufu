import { redirect } from 'next/navigation'
import { type Locale } from '@/i18n'

export default async function Home({
  params,
}: {
  params: Promise<{ locale: Locale }>
}) {
  const { locale } = await params
  // Redirect to login page with proper locale
  redirect(`/${locale}/login`)
}
