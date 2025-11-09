/**
 * CompanyBadge component
 * Displays verification status badge for importers/exporters
 */

import { Badge } from '@/components/ui/badge'
import { CheckCircle2, AlertTriangle } from 'lucide-react'

interface CompanyBadgeProps {
  isVerified: boolean
  declarationCount?: number
}

export function CompanyBadge({
  isVerified,
  declarationCount,
}: CompanyBadgeProps) {
  if (isVerified) {
    return (
      <Badge
        variant="default"
        className="bg-green-500 hover:bg-green-600 gap-1"
      >
        <CheckCircle2 className="h-3 w-3" />
        Verified Company
        {declarationCount !== undefined && declarationCount > 0 && (
          <span className="ml-1">({declarationCount} declarations)</span>
        )}
      </Badge>
    )
  }

  return (
    <Badge
      variant="secondary"
      className="bg-yellow-500 hover:bg-yellow-600 text-white gap-1"
    >
      <AlertTriangle className="h-3 w-3" />
      New Company - Review Required
    </Badge>
  )
}
