/**
 * useCompanies hook for managing company data with TanStack Query
 * Story 3.10: Master Data Management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getCompanies,
  getCompany,
  createCompany,
  updateCompany,
  deleteCompany,
  getDuplicates,
  mergeCompanies,
} from '@/lib/api'
import type {
  CompanyListParams,
  CompanyType,
  CompanyCreate,
  CompanyUpdate,
} from '@/types/company'

/**
 * Hook for fetching paginated company list
 */
export function useCompanies(params: CompanyListParams) {
  return useQuery({
    queryKey: [
      'companies',
      params.type,
      params.search,
      params.filter,
      params.page,
      params.sort_by,
      params.sort_order,
    ],
    queryFn: () => getCompanies(params),
  })
}

/**
 * Hook for fetching single company details
 */
export function useCompany(id: string | undefined, type: CompanyType) {
  return useQuery({
    queryKey: ['companies', id, type],
    queryFn: () => {
      if (!id) throw new Error('Company ID is required')
      return getCompany(id, type)
    },
    enabled: !!id,
  })
}

/**
 * Hook for creating a new company
 */
export function useCreateCompany() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ type, data }: { type: CompanyType; data: CompanyCreate }) =>
      createCompany(type, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })
}

/**
 * Hook for updating a company
 */
export function useUpdateCompany() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      type,
      data,
    }: {
      id: string
      type: CompanyType
      data: CompanyUpdate
    }) => updateCompany(id, type, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.invalidateQueries({ queryKey: ['companies', variables.id] })
    },
  })
}

/**
 * Hook for deleting a company
 */
export function useDeleteCompany() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, type }: { id: string; type: CompanyType }) =>
      deleteCompany(id, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })
}

/**
 * Hook for fetching duplicate companies
 */
export function useDuplicates(type: CompanyType) {
  return useQuery({
    queryKey: ['companies', 'duplicates', type],
    queryFn: () => getDuplicates(type),
  })
}

/**
 * Hook for merging two companies
 */
export function useMergeCompanies() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      type,
      keepId,
      mergeId,
    }: {
      type: CompanyType
      keepId: string
      mergeId: string
    }) => mergeCompanies(type, keepId, mergeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.invalidateQueries({ queryKey: ['companies', 'duplicates'] })
    },
  })
}
