/**
 * Modal for performing actions on alerts (acknowledge, resolve, assign, silence)
 */

import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Button, Input, Select } from '../ui'
import type { Alert, AlertActionRequest, AlertActionModalProps } from '../../types/alerts'

const SILENCE_DURATION_OPTIONS = [
  { value: '1h', label: '1 hour' },
  { value: '4h', label: '4 hours' },
  { value: '8h', label: '8 hours' },
  { value: '24h', label: '24 hours' },
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' }
]

export function AlertActionModal({
  alerts,
  action,
  isOpen,
  onClose,
  onConfirm
}: AlertActionModalProps) {
  const [assignee, setAssignee] = useState('')
  const [comment, setComment] = useState('')
  const [silenceDuration, setSilenceDuration] = useState('1h')
  const [loading, setLoading] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const request: AlertActionRequest = {
      alertIds: alerts.map(alert => alert.id),
      action,
      ...(comment && { comment }),
      ...(action === 'assign' && assignee && { assignee }),
      ...(action === 'silence' && { silenceDuration })
    }

    try {
      setLoading(true)
      await onConfirm(request)
      
      // Reset form
      setAssignee('')
      setComment('')
      setSilenceDuration('1h')
    } catch (error) {
      // Error handling is done by parent component
    } finally {
      setLoading(false)
    }
  }

  const getActionTitle = () => {
    switch (action) {
      case 'acknowledge':
        return 'Acknowledge Alerts'
      case 'resolve':
        return 'Resolve Alerts'
      case 'assign':
        return 'Assign Alerts'
      case 'silence':
        return 'Silence Alerts'
      default:
        return 'Alert Action'
    }
  }

  const getActionDescription = () => {
    const count = alerts.length
    const alertText = count === 1 ? 'alert' : 'alerts'
    
    switch (action) {
      case 'acknowledge':
        return `Mark ${count} ${alertText} as acknowledged. This indicates that someone is aware of the issue.`
      case 'resolve':
        return `Mark ${count} ${alertText} as resolved. This will close the alerts.`
      case 'assign':
        return `Assign ${count} ${alertText} to a team member for investigation.`
      case 'silence':
        return `Silence ${count} ${alertText} for a specified duration. Silenced alerts won't trigger notifications.`
      default:
        return `Perform action on ${count} ${alertText}.`
    }
  }

  const isFormValid = () => {
    if (action === 'assign' && !assignee.trim()) {
      return false
    }
    return true
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="sm:flex sm:items-start">
                <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-2">
                    {getActionTitle()}
                  </h3>
                  
                  <p className="text-sm text-gray-500 mb-4">
                    {getActionDescription()}
                  </p>

                  {/* Alert list */}
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      Selected Alerts ({alerts.length})
                    </h4>
                    <div className="max-h-32 overflow-y-auto border border-gray-200 rounded-md">
                      {alerts.map((alert) => (
                        <div
                          key={alert.id}
                          className="px-3 py-2 border-b border-gray-100 last:border-b-0"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-900 truncate">
                              {alert.title}
                            </span>
                            <span className={clsx(
                              'text-xs px-2 py-1 rounded-full',
                              alert.severity === 'critical' && 'bg-red-100 text-red-800',
                              alert.severity === 'high' && 'bg-orange-100 text-orange-800',
                              alert.severity === 'medium' && 'bg-yellow-100 text-yellow-800',
                              alert.severity === 'low' && 'bg-blue-100 text-blue-800',
                              alert.severity === 'info' && 'bg-gray-100 text-gray-800'
                            )}>
                              {alert.severity}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Action-specific fields */}
                  {action === 'assign' && (
                    <div className="mb-4">
                      <Input
                        label="Assignee"
                        placeholder="Enter username or email"
                        value={assignee}
                        onChange={(e) => setAssignee(e.target.value)}
                        required
                      />
                    </div>
                  )}

                  {action === 'silence' && (
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Silence Duration
                      </label>
                      <Select
                        value={silenceDuration}
                        onChange={setSilenceDuration}
                        options={SILENCE_DURATION_OPTIONS}
                      />
                    </div>
                  )}

                  {/* Comment field */}
                  <div className="mb-4">
                    <Input
                      label="Comment (optional)"
                      placeholder="Add a comment about this action..."
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      helperText={
                        action === 'acknowledge' 
                          ? "Explain what you're doing to address this alert"
                          : action === 'resolve'
                          ? "Explain how this issue was resolved"
                          : action === 'assign'
                          ? "Add context for the assignee"
                          : "Explain why you're silencing these alerts"
                      }
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <Button
                type="submit"
                variant={action === 'resolve' ? 'primary' : action === 'silence' ? 'secondary' : 'primary'}
                className="w-full sm:ml-3 sm:w-auto"
                disabled={!isFormValid() || loading}
                loading={loading}
              >
                {loading ? 'Processing...' : getActionTitle()}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="mt-3 w-full sm:mt-0 sm:w-auto"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}