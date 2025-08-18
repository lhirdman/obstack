/**
 * Alert notification preferences component
 */

import React, { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import { Button, Input, Select, Badge } from '../ui'
import { alertService } from '../../services/alert-service'
import type { AlertNotificationChannel, AlertNotificationRule } from '../../types/alerts'

export interface NotificationPreferencesProps {
  className?: string
}

const CHANNEL_TYPES = [
  { value: 'email', label: 'Email' },
  { value: 'slack', label: 'Slack' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'pagerduty', label: 'PagerDuty' },
  { value: 'teams', label: 'Microsoft Teams' }
]

const SEVERITY_OPTIONS = [
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
  { value: 'info', label: 'Info' }
]

export function NotificationPreferences({ className }: NotificationPreferencesProps) {
  const [channels, setChannels] = useState<AlertNotificationChannel[]>([])
  const [rules, setRules] = useState<AlertNotificationRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Channel form state
  const [showChannelForm, setShowChannelForm] = useState(false)
  const [channelForm, setChannelForm] = useState({
    name: '',
    type: 'email' as 'email' | 'slack' | 'webhook' | 'pagerduty' | 'teams',
    config: {} as Record<string, any>
  })
  
  // Rule form state
  const [showRuleForm, setShowRuleForm] = useState(false)
  const [ruleForm, setRuleForm] = useState({
    name: '',
    conditions: {
      severity: [] as string[],
      source: [] as string[],
      status: [] as string[]
    },
    channels: [] as string[]
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [channelsData, rulesData] = await Promise.all([
        alertService.getNotificationChannels(),
        alertService.getNotificationRules()
      ])
      
      setChannels(channelsData)
      setRules(rulesData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notification preferences')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateChannel = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const newChannel = await alertService.createNotificationChannel({
        name: channelForm.name,
        type: channelForm.type,
        config: channelForm.config,
        enabled: true,
        tenantId: '' // Will be set by backend
      })
      
      setChannels(prev => [...prev, newChannel])
      setChannelForm({ name: '', type: 'email', config: {} })
      setShowChannelForm(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create channel')
    }
  }

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const newRule = await alertService.createNotificationRule({
        name: ruleForm.name,
        conditions: ruleForm.conditions,
        channels: ruleForm.channels,
        enabled: true,
        tenantId: '' // Will be set by backend
      })
      
      setRules(prev => [...prev, newRule])
      setRuleForm({
        name: '',
        conditions: { severity: [], source: [], status: [] },
        channels: []
      })
      setShowRuleForm(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create rule')
    }
  }

  const handleToggleChannel = async (channelId: string, enabled: boolean) => {
    try {
      await alertService.updateNotificationChannel(channelId, { enabled })
      setChannels(prev => prev.map(channel => 
        channel.id === channelId ? { ...channel, enabled } : channel
      ))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update channel')
    }
  }

  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await alertService.updateNotificationRule(ruleId, { enabled })
      setRules(prev => prev.map(rule => 
        rule.id === ruleId ? { ...rule, enabled } : rule
      ))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update rule')
    }
  }

  const handleTestChannel = async (channelId: string) => {
    try {
      const result = await alertService.testNotificationChannel(channelId)
      if (result.success) {
        alert('Test notification sent successfully!')
      } else {
        alert(`Test failed: ${result.message}`)
      }
    } catch (err) {
      alert(`Test failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  const handleDeleteChannel = async (channelId: string) => {
    if (!confirm('Are you sure you want to delete this notification channel?')) return
    
    try {
      await alertService.deleteNotificationChannel(channelId)
      setChannels(prev => prev.filter(channel => channel.id !== channelId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete channel')
    }
  }

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this notification rule?')) return
    
    try {
      await alertService.deleteNotificationRule(ruleId)
      setRules(prev => prev.filter(rule => rule.id !== ruleId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete rule')
    }
  }

  const renderChannelConfig = () => {
    switch (channelForm.type) {
      case 'email':
        return (
          <Input
            label="Email Address"
            type="email"
            placeholder="alerts@example.com"
            value={channelForm.config.email || ''}
            onChange={(e) => setChannelForm(prev => ({
              ...prev,
              config: { ...prev.config, email: e.target.value }
            }))}
            required
          />
        )
      case 'slack':
        return (
          <Input
            label="Slack Webhook URL"
            placeholder="https://hooks.slack.com/services/..."
            value={channelForm.config.webhookUrl || ''}
            onChange={(e) => setChannelForm(prev => ({
              ...prev,
              config: { ...prev.config, webhookUrl: e.target.value }
            }))}
            required
          />
        )
      case 'webhook':
        return (
          <div className="space-y-4">
            <Input
              label="Webhook URL"
              placeholder="https://api.example.com/webhooks/alerts"
              value={channelForm.config.url || ''}
              onChange={(e) => setChannelForm(prev => ({
                ...prev,
                config: { ...prev.config, url: e.target.value }
              }))}
              required
            />
            <Input
              label="Secret (optional)"
              placeholder="Webhook secret for verification"
              value={channelForm.config.secret || ''}
              onChange={(e) => setChannelForm(prev => ({
                ...prev,
                config: { ...prev.config, secret: e.target.value }
              }))}
            />
          </div>
        )
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className={clsx('p-8 text-center', className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-sm text-gray-500">Loading notification preferences...</p>
      </div>
    )
  }

  return (
    <div className={clsx('space-y-8', className)}>
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Notification Preferences</h2>
        <p className="mt-1 text-sm text-gray-600">
          Configure how and when you receive alert notifications.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Notification Channels */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Notification Channels</h3>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowChannelForm(true)}
          >
            Add Channel
          </Button>
        </div>

        {channels.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No notification channels configured. Add one to get started.
          </p>
        ) : (
          <div className="space-y-4">
            {channels.map((channel) => (
              <div
                key={channel.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <Badge variant={channel.enabled ? 'success' : 'default'}>
                    {channel.type}
                  </Badge>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{channel.name}</h4>
                    <p className="text-xs text-gray-500">
                      {channel.type === 'email' && channel.config.email}
                      {channel.type === 'slack' && 'Slack webhook'}
                      {channel.type === 'webhook' && channel.config.url}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTestChannel(channel.id)}
                  >
                    Test
                  </Button>
                  <Button
                    variant={channel.enabled ? 'secondary' : 'primary'}
                    size="sm"
                    onClick={() => handleToggleChannel(channel.id, !channel.enabled)}
                  >
                    {channel.enabled ? 'Disable' : 'Enable'}
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDeleteChannel(channel.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Channel form */}
        {showChannelForm && (
          <div className="mt-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
            <form onSubmit={handleCreateChannel} className="space-y-4">
              <h4 className="text-sm font-medium text-gray-900">Add Notification Channel</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Channel Name"
                  placeholder="My Email Channel"
                  value={channelForm.name}
                  onChange={(e) => setChannelForm(prev => ({ ...prev, name: e.target.value }))}
                  required
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Channel Type
                  </label>
                  <Select
                    value={channelForm.type}
                    onChange={(value) => setChannelForm(prev => ({ 
                      ...prev, 
                      type: value as typeof prev.type,
                      config: {} // Reset config when type changes
                    }))}
                    options={CHANNEL_TYPES}
                  />
                </div>
              </div>

              {renderChannelConfig()}

              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowChannelForm(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Create Channel
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Notification Rules */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Notification Rules</h3>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowRuleForm(true)}
            disabled={channels.length === 0}
          >
            Add Rule
          </Button>
        </div>

        {rules.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No notification rules configured. Add one to define when notifications are sent.
          </p>
        ) : (
          <div className="space-y-4">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div>
                  <h4 className="text-sm font-medium text-gray-900">{rule.name}</h4>
                  <div className="flex items-center space-x-2 mt-1">
                    {rule.conditions.severity?.length > 0 && (
                      <Badge variant="warning" size="sm">
                        Severity: {rule.conditions.severity.join(', ')}
                      </Badge>
                    )}
                    {rule.conditions.source?.length > 0 && (
                      <Badge variant="info" size="sm">
                        Source: {rule.conditions.source.join(', ')}
                      </Badge>
                    )}
                    <Badge variant="default" size="sm">
                      {rule.channels.length} channel{rule.channels.length !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant={rule.enabled ? 'secondary' : 'primary'}
                    size="sm"
                    onClick={() => handleToggleRule(rule.id, !rule.enabled)}
                  >
                    {rule.enabled ? 'Disable' : 'Enable'}
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDeleteRule(rule.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Rule form */}
        {showRuleForm && (
          <div className="mt-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
            <form onSubmit={handleCreateRule} className="space-y-4">
              <h4 className="text-sm font-medium text-gray-900">Add Notification Rule</h4>
              
              <Input
                label="Rule Name"
                placeholder="Critical Alerts"
                value={ruleForm.name}
                onChange={(e) => setRuleForm(prev => ({ ...prev, name: e.target.value }))}
                required
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Severity Conditions
                </label>
                <div className="space-y-1">
                  {SEVERITY_OPTIONS.map((option) => (
                    <label key={option.value} className="flex items-center">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        checked={ruleForm.conditions.severity.includes(option.value)}
                        onChange={(e) => {
                          const newSeverity = e.target.checked
                            ? [...ruleForm.conditions.severity, option.value]
                            : ruleForm.conditions.severity.filter(s => s !== option.value)
                          setRuleForm(prev => ({
                            ...prev,
                            conditions: { ...prev.conditions, severity: newSeverity }
                          }))
                        }}
                      />
                      <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notification Channels
                </label>
                <div className="space-y-1">
                  {channels.filter(c => c.enabled).map((channel) => (
                    <label key={channel.id} className="flex items-center">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        checked={ruleForm.channels.includes(channel.id)}
                        onChange={(e) => {
                          const newChannels = e.target.checked
                            ? [...ruleForm.channels, channel.id]
                            : ruleForm.channels.filter(c => c !== channel.id)
                          setRuleForm(prev => ({ ...prev, channels: newChannels }))
                        }}
                      />
                      <span className="ml-2 text-sm text-gray-700">{channel.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowRuleForm(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Create Rule
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}