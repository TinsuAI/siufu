/**
 * Declaration Data Hook
 *
 * TanStack Query hook for fetching and updating declaration data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getDeclaration, patchDeclaration } from '@/lib/api'
import type { Declaration } from '@/types/declaration'

interface UseDeclarationResult {
  /**
   * The declaration data
   */
  declaration: Declaration | undefined
  /**
   * Whether the initial data is loading
   */
  isLoading: boolean
  /**
   * Whether there was an error loading the data
   */
  isError: boolean
  /**
   * The error object if there was an error
   */
  error: Error | null
  /**
   * Mutation function to update declaration draft data
   */
  updateDraftData: (draftData: Record<string, unknown>) => void
  /**
   * Whether an update is currently in progress
   */
  isUpdating: boolean
  /**
   * Whether the last update was successful
   */
  isUpdateSuccess: boolean
  /**
   * Whether the last update failed
   */
  isUpdateError: boolean
}

/**
 * Hook for fetching and updating declaration data
 * @param id - Declaration UUID
 * @returns Declaration data and update methods
 */
export function useDeclaration(id: string): UseDeclarationResult {
  const queryClient = useQueryClient()

  // Query for fetching declaration data
  const {
    data: declaration,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['declarations', id],
    queryFn: () => getDeclaration(id),
    // Poll every 2 seconds if processing
    refetchInterval: (query) => {
      const data = query.state.data as Declaration | undefined
      if (data?.status === 'PROCESSING') {
        return 2000
      }
      return false
    },
  })

  // Mutation for updating draft data
  const mutation = useMutation({
    mutationFn: (draftData: Record<string, unknown>) => {
      return patchDeclaration(id, draftData)
    },
    onSuccess: () => {
      // Invalidate and refetch declaration data
      queryClient.invalidateQueries({ queryKey: ['declarations', id] })
    },
    // Optionally implement optimistic updates
    onMutate: async (newDraftData) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['declarations', id] })

      // Snapshot the previous value
      const previousDeclaration = queryClient.getQueryData<Declaration>([
        'declarations',
        id,
      ])

      // Optimistically update to the new value
      if (previousDeclaration) {
        queryClient.setQueryData<Declaration>(['declarations', id], {
          ...previousDeclaration,
          draft_data: newDraftData as any,
        })
      }

      // Return context with previous value
      return { previousDeclaration }
    },
    onError: (_err, _newDraftData, context) => {
      // Rollback to previous value on error
      if (context?.previousDeclaration) {
        queryClient.setQueryData(
          ['declarations', id],
          context.previousDeclaration
        )
      }
    },
  })

  return {
    declaration: declaration as Declaration | undefined,
    isLoading,
    isError,
    error: error as Error | null,
    updateDraftData: mutation.mutate,
    isUpdating: mutation.isPending,
    isUpdateSuccess: mutation.isSuccess,
    isUpdateError: mutation.isError,
  }
}
