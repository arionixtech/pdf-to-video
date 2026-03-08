import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PDF to Video - Arionix Tech',
  description: 'Convert PDFs into engaging animated videos',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
