# Frontend Architecture

## Component Organization

```
frontend/src/
├── app/                          # Next.js 15 App Router
│   ├── (auth)/
│   │   └── login/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx            # Protected layout with nav
│   │   ├── declarations/
│   │   │   ├── page.tsx          # List view
│   │   │   └── [id]/review/page.tsx  # Review interface
│   │   ├── upload/page.tsx
│   │   ├── analytics/page.tsx
│   │   └── knowledge-base/page.tsx
│   └── layout.tsx
├── components/
│   ├── ui/                       # shadcn/ui components
│   ├── declarations/
│   │   ├── declaration-form.tsx
│   │   ├── declaration-table.tsx
│   │   └── validation-warnings.tsx
│   ├── pdf/
│   │   ├── pdf-viewer.tsx
│   │   └── pdf-toolbar.tsx
│   └── upload/
│       └── file-dropzone.tsx
├── hooks/
│   ├── use-declaration.ts        # TanStack Query hook
│   ├── use-auto-save.ts
│   └── use-auth.ts
├── lib/
│   ├── api-client.ts             # OpenAPI-generated client
│   └── validators.ts             # Zod schemas
├── stores/
│   ├── ui-store.ts               # Zustand (UI state)
│   └── auth-store.ts
└── types/
    └── index.ts
```

## State Management

**Zustand for UI State:**
```typescript
// stores/ui-store.ts
export const useUIStore = create<UIState>((set) => ({
  pdfZoom: 1.0,
  pdfCurrentPage: 1,
  activeDocumentTab: 'INVOICE',
  setPdfZoom: (zoom) => set({ pdfZoom: zoom }),
  // ... more UI state
}));
```

**TanStack Query for Server State:**
```typescript
// hooks/use-declaration.ts
export function useDeclaration(id: string) {
  const query = useQuery({
    queryKey: ['declarations', id],
    queryFn: () => apiClient.getDeclaration(id),
    refetchInterval: (data) => {
      // Poll every 2s if processing
      if (data?.status === 'PROCESSING') return 2000;
      return false;
    },
  });
  // ... mutations
}
```

---
