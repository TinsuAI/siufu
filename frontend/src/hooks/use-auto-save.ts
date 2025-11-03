/**
 * Auto-Save Hook
 *
 * Provides debounced auto-save functionality for forms using TanStack Query
 */

import { useEffect, useRef } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

interface UseAutoSaveOptions<T> {
  /**
   * Unique key for the data being saved (e.g., declaration ID)
   */
  key: string[]
  /**
   * Function to save data to the server
   * @param data - The data to save
   * @returns Promise that resolves when save is complete
   */
  saveFn: (data: T) => Promise<unknown>
  /**
   * Debounce delay in milliseconds (default: 5000)
   */
  debounceMs?: number
  /**
   * Whether auto-save is enabled (default: true)
   */
  enabled?: boolean
}

interface UseAutoSaveResult {
  /**
   * Whether a save operation is currently in progress
   */
  isSaving: boolean
  /**
   * Whether the last save was successful
   */
  isSuccess: boolean
  /**
   * Whether the last save failed
   */
  isError: boolean
  /**
   * Error from the last save attempt
   */
  error: Error | null
  /**
   * Manually trigger a save (bypasses debounce)
   */
  save: () => void
}

/**
 * Hook for auto-saving form data with debouncing
 * @param data - The current form data
 * @param options - Configuration options
 * @returns Auto-save state and controls
 */
export function useAutoSave<T>(
  data: T,
  options: UseAutoSaveOptions<T>
): UseAutoSaveResult {
  const { key, saveFn, debounceMs = 5000, enabled = true } = options

  const queryClient = useQueryClient()
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Mutation for saving data
  const mutation = useMutation({
    mutationFn: saveFn,
    onSuccess: () => {
      // Invalidate query to refetch fresh data
      queryClient.invalidateQueries({ queryKey: key })
    },
  })

  // Auto-save effect with debouncing
  useEffect(() => {
    if (!enabled) return

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Set new debounce timer
    debounceTimerRef.current = setTimeout(() => {
      mutation.mutate(data)
    }, debounceMs)

    // Cleanup on unmount or when data changes
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [data, enabled, debounceMs, mutation])

  // Manual save function (bypasses debounce)
  const save = () => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    mutation.mutate(data)
  }

  return {
    isSaving: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error as Error | null,
    save,
  }
}
