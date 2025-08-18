/**
 * Alert detail view component
 */

import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Button, Badge } from '../ui'
import { AlertActionModal } from './AlertActionModal'
import type { Alert, AlertActionRequest, AlertDetailViewProps } from '../../types/alerts'
import { SEVERITY_COLORS, STATUS_COLORS, SEVERITY_ICONS, STATUS_ICONS } from '../../types/alerts'

export function AlertDetail({
  alert,
  onClose,
  onAction
}: AlertDetailViewProps) {
  const [actionModal, setActionModal] = useState<{
    isOpen: boolean
    action: 'acknowledge' | 'resolve' | 'assign' | 'silence'
  }>({ isOpen: false, action: 'acknowledge' })

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const getDuration = () => {
    if (!alert.endsAt) {
      const now = new Date()
      const start = new Date(alert.startsAt)
      const durationMs = now.getTime() - start.getTime()
      const durationMins = Math.floor(durationMs / (1000 * 60))
      const durationHours = Math.floor(durationMins / 60)
      const durationDays = Math.floor(durationHours / 24)
      
      if (durationDays > 0) return `${durationDays}d ${durationHours % 24}h`
      if (durationHours > 0) return `${durationHours}h ${durationMins % 60}m`
      return `${durationMins}m`
    }
    
    const start = new Date(alert.startsAt)
    const end = new Date(alert.endsAt)
    const durationMs = end.getTime() - start.getTime()
    const durationMins = Math.floor(durationMs / (1000 * 60))
    const durationHours = Math.floor(durationMins / 60)
    
    if (durationHours > 0) return `${durationHours}h ${durationMins % 60}m`
    return `${durationMins}m`
  }

  const handleAction = (action: typeof actionModal.action) => {
    setActionModal({ isOpen: true, action })
  }

  const handleActionConfirm = async (request: AlertActionRequest) => {
    try {
      await onAction(request)
      setActionModal({ isOpen: false, action: 'acknowledge' })
    } catch (error) {
      // Error handling is done by parent component
      console.error('Action failed:', error)
    }
  }

  const canAcknowledge = alert.status === 'active'
  const canResolve = alert.status === 'active' || alert.status === 'acknowledged'
  const canAssign = alert.status !== 'resolved'
  const canSilence = alert.status === 'active' && !alert.silenceId

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-white px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <h2 className="text-xl font-semibold text-gray-900">
                  Alert Details
                </h2>
                <Badge
                  variant={SEVERITY_COLORS[alert.severity]}
                  size="md"
                >
                  {SEVERITY_ICONS[alert.severity]} {alert.severity.toUpperCase()}
                </Badge>
                <Badge
                  variant={STATUS_COLORS[alert.status]}
                  size="md"
                >
                  {STATUS_ICONS[alert.status]} {alert.status.toUpperCase()}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
              >
                ✕
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white px-6 py-4">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Main content */}
              <div className="lg:col-span-2 space-y-6">
                {/* Alert title and description */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {alert.title}
                  </h3>
                  {alert.description && (
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {alert.description}
                    </p>
                  )}
                </div>

                {/* Labels */}
                {Object.keys(alert.labels).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Labels</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {Object.entries(alert.labels).map(([key, value]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded-md"
                        >
                          <span className="text-sm font-medium text-gray-700">{key}</span>
                          <span className="text-sm text-gray-600 font-mono">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Annotations */}
                {Object.keys(alert.annotations).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Annotations</h4>
                    <div className="space-y-2">
                      {Object.entries(alert.annotations).map(([key, value]) => (
                        <div key={key} className="p-3 bg-gray-50 rounded-md">
                          <div className="text-sm font-medium text-gray-700 mb-1">{key}</div>
                          <div className="text-sm text-gray-600 whitespace-pre-wrap">{value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Timeline */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Timeline</h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      <span className="text-sm text-gray-600">
                        Started: {formatTimestamp(alert.startsAt)}
                      </span>
                    </div>
                    {alert.endsAt && (
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm text-gray-600">
                          Ended: {formatTimestamp(alert.endsAt)}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-sm text-gray-600">
                        Last updated: {formatTimestamp(alert.updatedAt)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Actions */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Actions</h4>
                  <div className="space-y-2">
                    {canAcknowledge && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => handleAction('acknowledge')}
                      >
                        👀 Acknowledge
                      </Button>
                    )}
                    {canResolve && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => handleAction('resolve')}
                      >
                        ✅ Resolve
                      </Button>
                    )}
                    {canAssign && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => handleAction('assign')}
                      >
                        👤 Assign
                      </Button>
                    )}
                    {canSilence && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => handleAction('silence')}
                      >
                        🔇 Silence
                      </Button>
                    )}
                  </div>
                </div>

                {/* Metadata */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Metadata</h4>
                  <div className="space-y-3">
                    <div>
                      <span className="text-xs text-gray-500 uppercase tracking-wide">Source</span>
                      <div className="text-sm text-gray-900">{alert.source}</div>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 uppercase tracking-wide">Duration</span>
                      <div className="text-sm text-gray-900">{getDuration()}</div>
                    </div>
                    {alert.assignee && (
                      <div>
                        <span className="text-xs text-gray-500 uppercase tracking-wide">Assignee</span>
                        <div className="text-sm text-gray-900">{alert.assignee}</div>
                      </div>
                    )}
                    <div>
                      <span className="text-xs text-gray-500 uppercase tracking-wide">Fingerprint</span>
                      <div className="text-xs text-gray-600 font-mono break-all">{alert.fingerprint}</div>
                    </div>
                    {alert.generatorUrl && (
                      <div>
                        <span className="text-xs text-gray-500 uppercase tracking-wide">Source URL</span>
                        <div>
                          <a
                            href={alert.generatorUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:text-blue-800 break-all"
                          >
                            View in source system
                          </a>
                        </div>
                      </div>
                    )}
                    {alert.silenceId && (
                      <div>
                        <span className="text-xs text-gray-500 uppercase tracking-wide">Silence</span>
                        <div className="text-sm text-gray-900">
                          <Badge variant="default" size="sm">
                            Silenced
                          </Badge>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action modal */}
      <AlertActionModal
        alerts={[alert]}
        action={actionModal.action}
        isOpen={actionModal.isOpen}
        onClose={() => setActionModal({ isOpen: false, action: 'acknowledge' })}
        onConfirm={handleActionConfirm}
      />
    </div>
  )
}