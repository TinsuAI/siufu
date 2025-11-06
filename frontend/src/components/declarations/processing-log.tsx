/**
 * Processing Log Component
 * Displays real-time processing activity logs
 */

import { ProcessingLogEntry } from '@/types/declaration'
import { Card } from '@/components/ui/card'
import { CheckCircle2, Info, AlertTriangle, XCircle, Clock } from 'lucide-react'
import { format } from 'date-fns'

interface ProcessingLogProps {
  logs: ProcessingLogEntry[]
}

export function ProcessingLog({ logs }: ProcessingLogProps) {
  if (!logs || logs.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Processing Activity</h3>
        <div className="text-center py-8 text-slate-500">
          <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>Processing has not started yet...</p>
        </div>
      </Card>
    )
  }

  const getIcon = (level: string) => {
    switch (level) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      default:
        return <Info className="h-4 w-4 text-blue-600" />
    }
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success':
        return 'bg-green-50 border-green-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200'
      default:
        return 'bg-blue-50 border-blue-200'
    }
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Clock className="h-5 w-5" />
        Processing Activity Log
      </h3>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {logs.map((log, index) => (
          <div
            key={index}
            className={`border rounded-lg p-3 ${getLevelColor(log.level)}`}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5">{getIcon(log.level)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="text-sm font-medium text-slate-900">
                    {log.message}
                  </p>
                  <span className="text-xs text-slate-500 whitespace-nowrap">
                    {format(new Date(log.timestamp), 'HH:mm:ss')}
                  </span>
                </div>
                {log.details && Object.keys(log.details).length > 0 && (
                  <div className="mt-2 text-xs text-slate-600 bg-white/50 rounded p-2">
                    {Object.entries(log.details).map(([key, value]) => (
                      <div key={key} className="flex gap-2">
                        <span className="font-medium">{key}:</span>
                        <span>{JSON.stringify(value)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
