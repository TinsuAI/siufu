import { useQuery } from '@tanstack/react-query'
import { getPDFFile } from '@/lib/api'

/**
 * TanStack Query hook for fetching PDF documents
 * Caches PDF files for 5 minutes (PDFs don't change)
 *
 * @param declarationId - Declaration UUID
 * @param filename - PDF filename (e.g., AN.pdf, BOL.pdf, CO_1.pdf, INVOICE.pdf)
 * @returns TanStack Query result with PDF Blob data
 */
export function usePDFDocument(declarationId: string, filename: string) {
  return useQuery({
    queryKey: ['declarations', declarationId, 'files', filename],
    queryFn: () => getPDFFile(declarationId, filename),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes (PDFs don't change)
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes (renamed from cacheTime in TanStack Query v5)
    enabled: !!declarationId && !!filename, // Only fetch if both params are provided
  })
}
