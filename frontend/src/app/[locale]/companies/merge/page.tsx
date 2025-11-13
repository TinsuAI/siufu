/**
 * Merge Duplicates Tool (Story 3.10)
 * Find and merge duplicate companies
 */

'use client'

import { Suspense, useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { useRouter } from '@/navigation'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  GitMerge,
  X,
} from 'lucide-react'
import { useDuplicates, useMergeCompanies } from '@/hooks/use-companies'
import type {
  CompanyType,
  ImporterListItem,
  ExporterListItem,
} from '@/types/company'
import { toast } from 'sonner'

function MergeDuplicatesContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const initialTab = (searchParams.get('type') || 'importers') as CompanyType
  const focusCompanyId = searchParams.get('focus')

  const [activeTab, setActiveTab] = useState<CompanyType>(initialTab)
  const [currentPairIndex, setCurrentPairIndex] = useState(0)
  const [selectedCompany, setSelectedCompany] = useState<
    'company1' | 'company2'
  >('company1')
  const focusHandledRef = useRef(false)

  // Fetch duplicates
  const {
    data: duplicates,
    isLoading,
    error,
    refetch,
  } = useDuplicates(activeTab)

  // Merge mutation
  const mergeMutation = useMergeCompanies()

  // Get current pair
  const currentPair = duplicates?.[currentPairIndex]

  useEffect(() => {
    if (!duplicates || !focusCompanyId || focusHandledRef.current) {
      return
    }
    const targetIndex = duplicates.findIndex(
      (pair) =>
        pair.company1.id === focusCompanyId ||
        pair.company2.id === focusCompanyId
    )
    if (targetIndex >= 0) {
      setCurrentPairIndex(targetIndex)
      setSelectedCompany(
        duplicates[targetIndex].company1.id === focusCompanyId
          ? 'company1'
          : 'company2'
      )
      focusHandledRef.current = true
    }
  }, [duplicates, focusCompanyId])

  // Handlers
  const handleMerge = async () => {
    if (!currentPair) return

    const keepId =
      selectedCompany === 'company1'
        ? currentPair.company1.id
        : currentPair.company2.id
    const mergeId =
      selectedCompany === 'company1'
        ? currentPair.company2.id
        : currentPair.company1.id
    const keepName =
      selectedCompany === 'company1'
        ? currentPair.company1.name
        : currentPair.company2.name
    const mergeName =
      selectedCompany === 'company1'
        ? currentPair.company2.name
        : currentPair.company1.name

    if (
      confirm(
        `Are you sure you want to merge "${mergeName}" into "${keepName}"?\n\nThis will:\n- Keep "${keepName}"\n- Delete "${mergeName}"\n- Transfer all declarations to "${keepName}"\n\nThis action cannot be undone.`
      )
    ) {
      try {
        const result = await mergeMutation.mutateAsync({
          type: activeTab,
          keepId,
          mergeId,
        })

        toast.success(
          `Companies merged successfully. ${result.declaration_count} declaration(s) now linked to ${keepName}.`
        )

        // Refresh duplicates list
        await refetch()

        // Move to next pair or reset if no more
        if (duplicates && currentPairIndex >= duplicates.length - 1) {
          setCurrentPairIndex(0)
        }
      } catch (error) {
        toast.error(`Failed to merge companies: ${(error as Error).message}`)
      }
    }
  }

  const handleSkip = () => {
    if (duplicates && currentPairIndex < duplicates.length - 1) {
      setCurrentPairIndex(currentPairIndex + 1)
      setSelectedCompany('company1') // Reset selection
    } else {
      setCurrentPairIndex(0)
      setSelectedCompany('company1')
    }
  }

  const handleTabChange = (value: string) => {
    setActiveTab(value as CompanyType)
    setCurrentPairIndex(0)
    setSelectedCompany('company1')
  }

  // Render company details
  const renderCompanyDetails = (
    company: ImporterListItem | ExporterListItem,
    side: 'company1' | 'company2'
  ) => {
    const isImporter = 'tax_code' in company
    const isSelected = selectedCompany === side

    return (
      <div
        className={`border rounded-lg p-4 cursor-pointer transition-all ${
          isSelected
            ? 'border-primary bg-primary/5 ring-2 ring-primary'
            : 'border-border hover:border-primary/50'
        }`}
        onClick={() => setSelectedCompany(side)}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <RadioGroupItem value={side} id={side} />
            <Label htmlFor={side} className="cursor-pointer">
              Keep this company
            </Label>
          </div>
          {company.is_verified && (
            <Badge variant="default" className="bg-green-500 text-xs">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Verified
            </Badge>
          )}
        </div>

        <div className="space-y-2">
          <div>
            <p className="text-sm text-muted-foreground">Name</p>
            <p className="font-medium">{company.name}</p>
          </div>

          {isImporter ? (
            <div>
              <p className="text-sm text-muted-foreground">Tax Code</p>
              <p className="font-medium">
                {(company as ImporterListItem).tax_code}
              </p>
            </div>
          ) : (
            <div>
              <p className="text-sm text-muted-foreground">Country</p>
              <p className="font-medium">
                {(company as ExporterListItem).country_code}
              </p>
            </div>
          )}

          <div>
            <p className="text-sm text-muted-foreground">Declarations</p>
            <p className="font-medium">{company.declaration_count}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground">Last Updated</p>
            <p className="font-medium">
              {new Date(company.updated_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/companies')}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Companies
        </Button>

        <h1 className="text-3xl font-bold flex items-center gap-3">
          <GitMerge className="h-8 w-8" />
          Merge Duplicates
        </h1>
        <p className="text-muted-foreground mt-1">
          Find and merge duplicate companies using fuzzy name matching
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="mb-6">
          <TabsTrigger value="importers">Importers</TabsTrigger>
          <TabsTrigger value="exporters">Exporters</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-0">
          {isLoading ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p>Scanning for duplicates...</p>
              </CardContent>
            </Card>
          ) : error ? (
            <Card>
              <CardContent className="py-12 text-center text-red-600">
                <p>Error loading duplicates: {error.message}</p>
              </CardContent>
            </Card>
          ) : !duplicates || duplicates.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-4 text-green-500" />
                <p className="text-lg font-medium">No duplicates found!</p>
                <p className="text-muted-foreground mt-2">
                  All {activeTab} appear to be unique.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Progress indicator */}
              <div className="mb-6">
                <p className="text-sm text-muted-foreground mb-2">
                  Duplicate {currentPairIndex + 1} of {duplicates.length}
                </p>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{
                      width: `${((currentPairIndex + 1) / duplicates.length) * 100}%`,
                    }}
                  />
                </div>
              </div>

              {/* Similarity Badge */}
              {currentPair && (
                <div className="flex items-center gap-2 mb-6">
                  <Badge
                    variant="secondary"
                    className="bg-yellow-500 text-white"
                  >
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    {Math.round(currentPair.similarity * 100)}% Similar
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {currentPair.reason}
                  </span>
                </div>
              )}

              {/* Comparison Card */}
              {currentPair && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle>Select Company to Keep</CardTitle>
                    <CardDescription>
                      Choose which company record to keep. The other will be
                      deleted and its declarations will be transferred.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <RadioGroup
                      value={selectedCompany}
                      onValueChange={(v) =>
                        setSelectedCompany(v as 'company1' | 'company2')
                      }
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {renderCompanyDetails(currentPair.company1, 'company1')}
                        {renderCompanyDetails(currentPair.company2, 'company2')}
                      </div>
                    </RadioGroup>
                  </CardContent>
                </Card>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4 justify-center">
                <Button
                  onClick={handleMerge}
                  disabled={mergeMutation.isPending}
                  size="lg"
                >
                  <GitMerge className="h-4 w-4 mr-2" />
                  {mergeMutation.isPending ? 'Merging...' : 'Confirm Merge'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleSkip}
                  disabled={mergeMutation.isPending}
                  size="lg"
                >
                  <X className="h-4 w-4 mr-2" />
                  Skip
                </Button>
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default function MergeDuplicatesPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <div className="text-center py-12">Loading...</div>
        </div>
      }
    >
      <MergeDuplicatesContent />
    </Suspense>
  )
}
