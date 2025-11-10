import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import '@/polyfills/promise-with-resolvers'
import { QueryProvider } from '@/components/providers/query-provider'
import { PDFProvider } from '@/components/providers/pdf-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Customs Declaration Automation Platform',
  description:
    'Automated customs declaration processing for logistics operations',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html>
      <body className={inter.className}>
        <QueryProvider>
          <PDFProvider>{children}</PDFProvider>
        </QueryProvider>
      </body>
    </html>
  )
}
