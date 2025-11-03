'use client'

import { useEffect } from 'react'
import { pdfjs } from 'react-pdf'

/**
 * PDFProvider component to configure react-pdf worker
 * Required for react-pdf 9.x to work properly
 */
export function PDFProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Configure PDF.js worker source
    // Using CDN for worker to avoid bundling issues
    pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`
  }, [])

  return <>{children}</>
}
