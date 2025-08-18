/**
 * Main Alerts view with comprehensive alert management
 */

import React, { useState } from 'react'
import { AlertList, AlertDetail, NotificationPreferences } from '../components/alerts'
import { Button } from '../components/ui'
import type { Alert, AlertActionRequest } from '../types/alerts'

type ViewMode = 'list' | 'preferences'

export default function Alerts() {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)

  const handleAlertClick = (alert: Alert) => {
    setSelectedAlert(alert)
  }

  const handleAlertAction = async (request: AlertActionRequest) => {
    // The action will be handled by the AlertDetail component
    // which will call the alert service and refresh the data
    console.log('Alert action performed:', request)
  }

  const handleCloseDetail = () => {
    setSelectedAlert(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setViewMode('list')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  viewMode === 'list'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Alert List
              </button>
              <button
                onClick={() => setViewMode('preferences')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  viewMode === 'preferences'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Notification Preferences
              </button>
            </nav>
          </div>
        </div>

        {/* Content */}
        {viewMode === 'list' && (
          <AlertList
            onAlertClick={handleAlertClick}
            autoRefresh={true}
            refreshInterval={30000}
          />
        )}

        {viewMode === 'preferences' && (
          <NotificationPreferences />
        )}

        {/* Alert detail modal */}
        {selectedAlert && (
          <AlertDetail
            alert={selectedAlert}
            onClose={handleCloseDetail}
            onAction={handleAlertAction}
          />
        )}
      </div>
    </div>
  )
}
