import React from 'react'
import type { SourceMetadataMap } from '@/lib/jump-navigation'

const SourceMetadataContext = React.createContext<
  SourceMetadataMap | null | undefined
>(null)

interface SourceMetadataProviderProps {
  value: SourceMetadataMap | null | undefined
  children: React.ReactNode
}

export function SourceMetadataProvider({
  value,
  children,
}: SourceMetadataProviderProps) {
  return (
    <SourceMetadataContext.Provider value={value}>
      {children}
    </SourceMetadataContext.Provider>
  )
}

export function useSourceMetadata() {
  return React.useContext(SourceMetadataContext)
}
