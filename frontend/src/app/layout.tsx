import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Customs Declaration Automation Platform',
  description: 'Automated customs declaration processing for logistics operations',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
