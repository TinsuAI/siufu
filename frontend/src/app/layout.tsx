import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import '@/polyfills/promise-with-resolvers'
import { Header } from '@/components/layout/header'
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
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <PDFProvider>
            <Header />
            <main className="min-h-[calc(100vh-4rem)]">{children}</main>
          </PDFProvider>
        </QueryProvider>
      </body>
    </html>
  )
}
