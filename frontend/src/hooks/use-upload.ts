/**
 * Upload hooks using TanStack Query
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { uploadDeclaration } from '@/lib/api';
import { useUploadStore } from '@/stores/upload-store';
import type { FileUploadState, UploadResponse } from '@/types/upload';

/**
 * Hook to upload declaration files
 * Returns mutation with loading state, error handling, and auto-navigation on success
 */
export function useUploadDeclaration() {
  const router = useRouter();
  const { setUploading, reset } = useUploadStore();
  const queryClient = useQueryClient();

  return useMutation<UploadResponse, Error, FileUploadState>({
    mutationFn: (files: FileUploadState) => uploadDeclaration(files),
    onMutate: () => {
      // Set uploading state to true when mutation starts
      setUploading(true);
    },
    onSuccess: (data) => {
      // Reset upload store
      reset();

      // Invalidate declarations query to refetch list
      queryClient.invalidateQueries({ queryKey: ['declarations'] });

      // Navigate to processing status page with declaration ID
      router.push(`/declarations/${data.declaration_id}`);
    },
    onError: (error) => {
      // Reset uploading state on error
      setUploading(false);
      // Error will be handled by the component
      void error; // Suppress unused variable warning
    },
    onSettled: () => {
      // Always reset uploading state when mutation completes
      setUploading(false);
    },
  });
}
