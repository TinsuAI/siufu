/**
 * Declaration Data Hook
 *
 * TanStack Query hook for fetching and updating declaration data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getDeclaration,
  patchDeclaration,
  approveDeclaration,
  rejectDeclaration,
  exportDeclaration,
} from '@/lib/api'
import type { Declaration, DraftData } from '@/types/declaration'

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
  /**
   * Approve declaration mutation
   */
  approveDeclaration: () => void
  /**
   * Whether approval is in progress
   */
  isApproving: boolean
  /**
   * Whether approval was successful
   */
  isApproveSuccess: boolean
  /**
   * Whether approval failed
   */
  isApproveError: boolean
  /**
   * Reject declaration mutation
   */
  rejectDeclaration: (rejectionReason: string) => void
  /**
   * Whether rejection is in progress
   */
  isRejecting: boolean
  /**
   * Whether rejection was successful
   */
  isRejectSuccess: boolean
  /**
   * Whether rejection failed
   */
  isRejectError: boolean
  /**
   * Export declaration to Excel mutation
   */
  exportDeclarationToExcel: () => void
  /**
   * Whether export is in progress
   */
  isExporting: boolean
  /**
   * Whether export was successful
   */
  isExportSuccess: boolean
  /**
   * Whether export failed
   */
  isExportError: boolean
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
          draft_data: newDraftData as DraftData,
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

  // Mutation for approving declaration
  const approveMutation = useMutation({
    mutationFn: () => approveDeclaration(id),
    onSuccess: () => {
      // Invalidate both declaration and declarations list
      queryClient.invalidateQueries({ queryKey: ['declarations', id] })
      queryClient.invalidateQueries({ queryKey: ['declarations'] })
    },
  })

  // Mutation for rejecting declaration
  const rejectMutation = useMutation({
    mutationFn: (rejectionReason: string) =>
      rejectDeclaration(id, rejectionReason),
    onSuccess: () => {
      // Invalidate both declaration and declarations list
      queryClient.invalidateQueries({ queryKey: ['declarations', id] })
      queryClient.invalidateQueries({ queryKey: ['declarations'] })
    },
  })

  // Mutation for exporting declaration to Excel
  const exportMutation = useMutation({
    mutationFn: () => exportDeclaration(id),
    onSuccess: (blob) => {
      // Trigger file download
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `CD_${id}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
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
    approveDeclaration: approveMutation.mutate,
    isApproving: approveMutation.isPending,
    isApproveSuccess: approveMutation.isSuccess,
    isApproveError: approveMutation.isError,
    rejectDeclaration: rejectMutation.mutate,
    isRejecting: rejectMutation.isPending,
    isRejectSuccess: rejectMutation.isSuccess,
    isRejectError: rejectMutation.isError,
    exportDeclarationToExcel: exportMutation.mutate,
    isExporting: exportMutation.isPending,
    isExportSuccess: exportMutation.isSuccess,
    isExportError: exportMutation.isError,
  }
}
