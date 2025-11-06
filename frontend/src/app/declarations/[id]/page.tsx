/**
 * Processing Status Page
 * Displays real-time progress while declaration is being processed
 */

'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  useDeclarationStatus,
  useRetryProcessing,
} from '@/hooks/use-declaration-status'
import { ProcessingStepper } from '@/components/declarations/processing-stepper'
import { ProcessingLog } from '@/components/declarations/processing-log'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DeclarationStatus } from '@/types/declaration'
import { Loader2, AlertCircle } from 'lucide-react'

/**
 * Maximum retry attempts before showing "Contact Support"
 */
const MAX_RETRY_ATTEMPTS = 3

/**
 * Session storage key for retry attempts
 */
const RETRY_COUNT_KEY = 'declaration_retry_count'

export default function ProcessingStatusPage() {
  const params = useParams()
  const router = useRouter()
  const declarationId = params.id as string

  // Fetch status with polling
  const {
    data: statusData,
    isLoading,
    isError,
    error,
    estimatedTimeRemaining,
    elapsedTime,
    isPolling,
  } = useDeclarationStatus(declarationId)

  // Retry mutation
  const retryMutation = useRetryProcessing()

  // Track retry attempts in component state
  const [retryAttempts, setRetryAttempts] = useState(0)
  const [showRedirectMessage, setShowRedirectMessage] = useState(false)

  // Load retry count from sessionStorage on mount
  useEffect(() => {
    const storedCount = sessionStorage.getItem(
      `${RETRY_COUNT_KEY}_${declarationId}`
    )
    if (storedCount) {
      setRetryAttempts(parseInt(storedCount, 10))
    }
  }, [declarationId])

  // Auto-redirect when status changes to READY_FOR_REVIEW
  useEffect(() => {
    if (statusData?.status === DeclarationStatus.READY_FOR_REVIEW) {
      setShowRedirectMessage(true)
      // Redirect after 2 second delay
      const timeout = setTimeout(() => {
        router.push(`/declarations/${declarationId}/review`)
      }, 2000)
      return () => clearTimeout(timeout)
    }
  }, [statusData?.status, declarationId, router])

  /**
   * Handle retry button click
   */
  const handleRetry = async () => {
    try {
      await retryMutation.mutateAsync(declarationId)
      // Increment retry count
      const newCount = retryAttempts + 1
      setRetryAttempts(newCount)
      sessionStorage.setItem(
        `${RETRY_COUNT_KEY}_${declarationId}`,
        newCount.toString()
      )
    } catch (error) {
      // Error will be shown by the mutation
      // eslint-disable-next-line no-console
      console.error('Retry failed:', error)
    }
  }

  /**
   * Format time in MM:SS format
   */
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto" />
          <p className="text-gray-600">Loading status...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <Card className="p-8 max-w-md w-full text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h1 className="text-2xl font-bold text-gray-900">
            Error Loading Status
          </h1>
          <p className="text-gray-600">
            {error?.message || 'Failed to load declaration status'}
          </p>
          <Button onClick={() => router.push('/upload')} className="w-full">
            Upload New Declaration
          </Button>
        </Card>
      </div>
    )
  }

  if (!statusData) return null

  const isFailed = statusData.status === DeclarationStatus.FAILED
  const showRetryButton = isFailed && retryAttempts < MAX_RETRY_ATTEMPTS
  const showContactSupport = isFailed && retryAttempts >= MAX_RETRY_ATTEMPTS

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Breadcrumb */}
      <div className="mb-6 text-sm text-gray-600">
        <span>Home</span> &gt; <span>Declarations</span> &gt;{' '}
        <span className="font-medium">Processing Status</span>
      </div>

      {/* Page Title */}
      <h1 className="text-3xl font-bold mb-2">
        {isFailed
          ? 'Processing Failed'
          : showRedirectMessage
            ? 'Processing Complete!'
            : `Processing Declaration #${declarationId.slice(0, 8)}...`}
      </h1>

      {/* Main Card */}
      <Card className="p-8 space-y-8">
        {/* Redirect Message */}
        {showRedirectMessage && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
            <p className="text-green-800 font-medium">
              Processing complete! Redirecting to review page...
            </p>
          </div>
        )}

        {/* Processing Stepper */}
        <ProcessingStepper
          status={statusData.status}
          progress={statusData.processing_progress}
        />

        {/* Time Information */}
        {!isFailed && !showRedirectMessage && (
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="space-y-1">
              <p className="text-sm text-gray-600">Elapsed Time</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatTime(elapsedTime)}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-gray-600">Estimated Time Remaining</p>
              <p className="text-2xl font-bold text-blue-600">
                ~{formatTime(estimatedTimeRemaining)}
              </p>
            </div>
          </div>
        )}

        {/* Processing Log */}
        {!showRedirectMessage && (
          <ProcessingLog logs={statusData.processing_log || []} />
        )}

        {/* Background Processing Message */}
        {isPolling && !isFailed && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
            <p className="text-sm text-blue-800">
              You can safely close this page - processing will continue in
              background
            </p>
          </div>
        )}

        {/* Failed State */}
        {isFailed && (
          <div className="space-y-4">
            {/* Error Message */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-red-800 font-medium">Processing Error</p>
                  <p className="text-red-700 text-sm mt-1">
                    {statusData.processing_error ||
                      'An unknown error occurred during processing'}
                  </p>
                </div>
              </div>
            </div>

            {/* Retry Button */}
            {showRetryButton && (
              <Button
                onClick={handleRetry}
                disabled={retryMutation.isPending}
                className="w-full"
                variant="default"
              >
                {retryMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  `Retry Processing (${retryAttempts}/${MAX_RETRY_ATTEMPTS})`
                )}
              </Button>
            )}

            {/* Contact Support */}
            {showContactSupport && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-900 font-medium">Contact Support</p>
                <p className="text-yellow-800 text-sm mt-1">
                  Error processing declaration #{declarationId.slice(0, 8)}.
                  Please contact support with this ID for troubleshooting.
                </p>
              </div>
            )}

            {/* Upload New Declaration */}
            <Button
              onClick={() => router.push('/upload')}
              className="w-full"
              variant="outline"
            >
              Upload New Declaration
            </Button>

            {/* Retry Error */}
            {retryMutation.isError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 text-sm">
                  {retryMutation.error?.message || 'Failed to retry processing'}
                </p>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}
