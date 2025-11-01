/**
 * Processing Stage Stepper Component
 * Visual progress indicator for declaration processing stages
 */

import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  ProcessingStage,
  DeclarationStatus,
  STAGE_LABELS,
  mapStatusToStage,
} from '@/types/declaration'
import { cn } from '@/lib/utils'
import {
  Upload,
  ScanText,
  Brain,
  CheckCircle,
  FileSpreadsheet,
  Check,
} from 'lucide-react'

/**
 * Icon mapping for each processing stage
 */
const STAGE_ICONS = {
  [ProcessingStage.UPLOADING]: Upload,
  [ProcessingStage.OCR_PROCESSING]: ScanText,
  [ProcessingStage.AI_EXTRACTION]: Brain,
  [ProcessingStage.VALIDATING]: CheckCircle,
  [ProcessingStage.GENERATING_EXCEL]: FileSpreadsheet,
  [ProcessingStage.READY_FOR_REVIEW]: Check,
}

/**
 * All stages in order
 */
const ALL_STAGES = [
  ProcessingStage.UPLOADING,
  ProcessingStage.OCR_PROCESSING,
  ProcessingStage.AI_EXTRACTION,
  ProcessingStage.VALIDATING,
  ProcessingStage.GENERATING_EXCEL,
  ProcessingStage.READY_FOR_REVIEW,
]

interface ProcessingStepperProps {
  status: DeclarationStatus
  progress: number // 0.0 to 1.0
  className?: string
}

/**
 * ProcessingStepper Component
 * Displays current processing stage with visual indicators
 */
export function ProcessingStepper({
  status,
  progress,
  className,
}: ProcessingStepperProps) {
  // Map backend status to frontend stage
  const currentStage = mapStatusToStage(status, progress)
  const currentStageIndex = ALL_STAGES.indexOf(currentStage)

  // Convert progress to percentage (0-100)
  const progressPercentage = Math.round(progress * 100)

  return (
    <div className={cn('w-full space-y-6', className)}>
      {/* Stage Indicators */}
      <div className="relative flex items-center justify-between">
        {ALL_STAGES.map((stage, index) => {
          const Icon = STAGE_ICONS[stage]
          const isActive = index === currentStageIndex
          const isCompleted = index < currentStageIndex
          const isPending = index > currentStageIndex

          return (
            <div key={stage} className="flex flex-col items-center flex-1">
              {/* Icon */}
              <div
                className={cn(
                  'flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300',
                  {
                    // Active stage - blue with pulse animation
                    'border-blue-500 bg-blue-50 text-blue-600 animate-pulse':
                      isActive,
                    // Completed stage - green with checkmark
                    'border-green-500 bg-green-50 text-green-600': isCompleted,
                    // Pending stage - gray
                    'border-gray-300 bg-gray-50 text-gray-400': isPending,
                  }
                )}
              >
                <Icon className="w-6 h-6" />
              </div>

              {/* Stage Label */}
              <div className="mt-2 text-center">
                <Badge
                  variant={
                    isActive ? 'default' : isCompleted ? 'secondary' : 'outline'
                  }
                  className={cn('text-xs', {
                    'bg-blue-500 text-white': isActive,
                    'bg-green-500 text-white': isCompleted,
                  })}
                >
                  {STAGE_LABELS[stage]}
                </Badge>
              </div>

              {/* Connector Line (except for last stage) */}
              {index < ALL_STAGES.length - 1 && (
                <div
                  className={cn(
                    'absolute top-6 h-0.5 transition-all duration-300',
                    {
                      'bg-green-500': isCompleted,
                      'bg-gray-300': !isCompleted,
                    }
                  )}
                  style={{
                    left: `${(100 / ALL_STAGES.length) * (index + 0.5)}%`,
                    width: `${100 / ALL_STAGES.length}%`,
                  }}
                />
              )}
            </div>
          )
        })}
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Processing Progress</span>
          <span className="font-semibold">{progressPercentage}%</span>
        </div>
        <Progress value={progressPercentage} className="h-2" />
      </div>

      {/* Current Stage Message */}
      <div className="text-center">
        <p className="text-sm text-gray-600">
          {status === DeclarationStatus.FAILED ? (
            <span className="text-red-600 font-medium">Processing Failed</span>
          ) : (
            <span>
              Currently:{' '}
              <span className="font-medium">{STAGE_LABELS[currentStage]}</span>
            </span>
          )}
        </p>
      </div>
    </div>
  )
}
