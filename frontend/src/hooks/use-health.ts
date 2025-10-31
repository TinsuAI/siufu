import { useQuery } from '@tanstack/react-query'
import { getHealthStatus } from '@/lib/api'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealthStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
  })
}
