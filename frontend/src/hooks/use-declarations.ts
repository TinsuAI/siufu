/**
 * Custom hook for fetching declarations using TanStack Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Declaration {
  id: number
  declaration_number: string
  status: string
  importer_name: string
  created_at: string
  updated_at: string
}

export interface CreateDeclarationInput {
  importer_name: string
  importer_address: string
  total_value: number
  currency: string
}

/**
 * Fetch all declarations
 */
export function useDeclarations() {
  return useQuery({
    queryKey: ['declarations'],
    queryFn: async (): Promise<Declaration[]> => {
      const response = await fetch(`${API_BASE_URL}/api/declarations`)
      if (!response.ok) {
        throw new Error('Failed to fetch declarations')
      }
      return response.json()
    }
  })
}

/**
 * Fetch a single declaration by ID
 */
export function useDeclaration(id: number) {
  return useQuery({
    queryKey: ['declarations', id],
    queryFn: async (): Promise<Declaration> => {
      const response = await fetch(`${API_BASE_URL}/api/declarations/${id}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch declaration ${id}`)
      }
      return response.json()
    },
    enabled: !!id  // Only run query if ID is provided
  })
}

/**
 * Create a new declaration
 */
export function useCreateDeclaration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: CreateDeclarationInput): Promise<Declaration> => {
      const response = await fetch(`${API_BASE_URL}/api/declarations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        throw new Error('Failed to create declaration')
      }

      return response.json()
    },
    // Invalidate and refetch declarations list after successful creation
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['declarations'] })
    }
  })
}
