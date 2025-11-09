/**
 * Status polling hook using TanStack Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useMemo } from 'react'
import { getDeclarationStatus, retryProcessing } from '@/lib/api'
import { isTerminalStatus, isProcessingStatus } from '@/types/declaration'
import type {
  StatusResponse,
  RetryProcessingResponse,
} from '@/types/declaration'

/**
 * Hook to poll declaration status with automatic refetch
 * @param id - Declaration UUID
 * @returns Query state with status data and estimated time remaining
 */
export function useDeclarationStatus(id: string) {
  const disableRetry = process.env.NODE_ENV === 'test'
  const query = useQuery<StatusResponse, Error>({
    queryKey: ['declarations', id, 'status'],
    queryFn: () => getDeclarationStatus(id),
    // Poll every 2 seconds while processing, stop when terminal
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return false

      // Stop polling for terminal states
      if (isTerminalStatus(data.status)) {
        return false
      }

      // Poll every 2 seconds for processing states
      if (isProcessingStatus(data.status)) {
        return 2000
      }

      return false
    },
    // Resume polling when user returns to tab
    refetchOnWindowFocus: true,
    // Retry on error with exponential backoff (3 retries)
    retry: disableRetry ? false : 3,
    retryDelay: disableRetry
      ? undefined
      : (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Keep previous data while refetching
    placeholderData: (previousData) => previousData,
  })

  /**
   * Calculate estimated time remaining (in seconds)
   * Based on 90 second average processing time
   */
  const estimatedTimeRemaining = useMemo(() => {
    if (!query.data?.created_at) return 90

    const createdAt = new Date(query.data.created_at).getTime()
    const now = Date.now()
    const elapsedSeconds = (now - createdAt) / 1000

    // Return max(0, 90 - elapsed)
    return Math.max(0, Math.round(90 - elapsedSeconds))
  }, [query.data?.created_at])

  /**
   * Calculate elapsed time (in seconds)
   */
  const elapsedTime = useMemo(() => {
    if (!query.data?.created_at) return 0

    const createdAt = new Date(query.data.created_at).getTime()
    const now = Date.now()
    return Math.round((now - createdAt) / 1000)
  }, [query.data?.created_at])

  /**
   * Check if currently polling
   */
  const isPolling = useMemo(() => {
    if (!query.data) return false
    return isProcessingStatus(query.data.status)
  }, [query.data])

  return {
    ...query,
    estimatedTimeRemaining,
    elapsedTime,
    isPolling,
  }
}

/**
 * Hook to retry processing for a failed declaration
 * @returns Mutation with retry functionality
 */
export function useRetryProcessing() {
  const queryClient = useQueryClient()

  return useMutation<RetryProcessingResponse, Error, string>({
    mutationFn: (id: string) => retryProcessing(id),
    onSuccess: (data, id) => {
      // Invalidate status query to immediately refetch
      queryClient.invalidateQueries({
        queryKey: ['declarations', id, 'status'],
      })
    },
  })
}
