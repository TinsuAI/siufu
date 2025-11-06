/**
 * Hook for managing declarations list with pagination, filtering, and sorting
 * Story 3.9: Declaration History List
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getDeclarations, deleteDeclaration } from '@/lib/api'
import type {
  DeclarationListParams,
  DeclarationListResponse,
} from '@/types/declaration'

export interface UseDeclarationsOptions extends DeclarationListParams {
  enabled?: boolean // Allow disabling the query
}

export function useDeclarations(options: UseDeclarationsOptions = {}) {
  const queryClient = useQueryClient()

  // Extract query parameters
  const {
    page = 1,
    limit = 20,
    status,
    search,
    sort_by = 'created_at',
    sort_order = 'desc',
    enabled = true,
  } = options

  // Fetch declarations list
  const query = useQuery<DeclarationListResponse, Error>({
    queryKey: [
      'declarations',
      'list',
      page,
      limit,
      status,
      search,
      sort_by,
      sort_order,
    ],
    queryFn: () =>
      getDeclarations({
        page,
        limit,
        status,
        search,
        sort_by,
        sort_order,
      }),
    enabled,
    // Keep previous data while fetching new page (better UX - no flash of empty state)
    placeholderData: (previousData) => previousData,
    // Stale time: 30 seconds (reduce refetches for same params)
    staleTime: 30000,
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (declarationId: string) => deleteDeclaration(declarationId),
    onSuccess: () => {
      // Invalidate declarations list query to trigger refetch
      queryClient.invalidateQueries({
        queryKey: ['declarations', 'list'],
      })
    },
  })

  return {
    data: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    deleteMutation,
  }
}
