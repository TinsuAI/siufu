/**
 * Declaration Status Badge Component
 *
 * Displays status badges with appropriate colors for declaration statuses
 */
import { Badge } from '@/components/ui/badge'

interface DeclarationStatusBadgeProps {
  status: string
}

export function DeclarationStatusBadge({
  status,
}: DeclarationStatusBadgeProps) {
  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return { className: 'bg-green-100 text-green-800 border-green-200' }
      case 'REJECTED':
        return { className: 'bg-red-100 text-red-800 border-red-200' }
      case 'READY_FOR_REVIEW':
        return { className: 'bg-blue-100 text-blue-800 border-blue-200' }
      case 'PROCESSING':
      case 'PROCESSING_OCR':
      case 'PROCESSING_LLM':
      case 'VALIDATING':
        return { className: 'bg-yellow-100 text-yellow-800 border-yellow-200' }
      case 'FAILED':
        return { className: 'bg-gray-100 text-gray-800 border-gray-200' }
      case 'UPLOADED':
        return { className: 'bg-slate-100 text-slate-800 border-slate-200' }
      default:
        return { className: 'bg-slate-100 text-slate-800 border-slate-200' }
    }
  }

  const style = getStatusStyle(status)

  return (
    <Badge className={style.className} variant="outline">
      {status.replace(/_/g, ' ')}
    </Badge>
  )
}
