/**
 * Alert management API service
 */

import { apiClient } from '../lib/api-client'
import type {
  Alert,
  AlertQuery,
  AlertsResponse,
  AlertActionRequest,
  AlertActionResponse,
  AlertStatistics,
  Silence,
  SilenceRequest,
  AlertNotificationChannel,
  AlertNotificationRule
} from '../types/alerts'

export class AlertService {
  /**
   * Get alerts with filtering and pagination
   */
  async getAlerts(query: AlertQuery = {}): Promise<AlertsResponse> {
    const params = new URLSearchParams()
    
    if (query.status?.length) {
      query.status.forEach(status => params.append('status', status))
    }
    if (query.severity?.length) {
      query.severity.forEach(severity => params.append('severity', severity))
    }
    if (query.source?.length) {
      query.source.forEach(source => params.append('source', source))
    }
    if (query.assignee) {
      params.append('assignee', query.assignee)
    }
    if (query.fromTime) {
      params.append('from_time', query.fromTime)
    }
    if (query.toTime) {
      params.append('to_time', query.toTime)
    }
    if (query.limit) {
      params.append('limit', query.limit.toString())
    }
    if (query.offset) {
      params.append('offset', query.offset.toString())
    }
    if (query.sortBy) {
      params.append('sort_by', query.sortBy)
    }
    if (query.sortOrder) {
      params.append('sort_order', query.sortOrder)
    }

    const queryString = params.toString()
    const url = queryString ? `/alerts?${queryString}` : '/alerts'
    
    return apiClient.get<AlertsResponse>(url)
  }

  /**
   * Get a specific alert by ID
   */
  async getAlert(alertId: string): Promise<Alert> {
    return apiClient.get<Alert>(`/alerts/${alertId}`)
  }

  /**
   * Perform action on alerts (acknowledge, resolve, assign, silence)
   */
  async performAction(request: AlertActionRequest): Promise<AlertActionResponse> {
    return apiClient.post<AlertActionResponse>('/alerts/actions', request)
  }

  /**
   * Get alert statistics
   */
  async getStatistics(): Promise<AlertStatistics> {
    return apiClient.get<AlertStatistics>('/alerts/statistics')
  }

  /**
   * Create a silence
   */
  async createSilence(request: SilenceRequest): Promise<Silence> {
    return apiClient.post<Silence>('/alerts/silences', request)
  }

  /**
   * Get active silences
   */
  async getSilences(): Promise<Silence[]> {
    return apiClient.get<Silence[]>('/alerts/silences')
  }

  /**
   * Delete a silence
   */
  async deleteSilence(silenceId: string): Promise<void> {
    return apiClient.delete(`/alerts/silences/${silenceId}`)
  }

  /**
   * Get notification channels
   */
  async getNotificationChannels(): Promise<AlertNotificationChannel[]> {
    return apiClient.get<AlertNotificationChannel[]>('/alerts/notification-channels')
  }

  /**
   * Create notification channel
   */
  async createNotificationChannel(channel: Omit<AlertNotificationChannel, 'id' | 'createdAt' | 'updatedAt'>): Promise<AlertNotificationChannel> {
    return apiClient.post<AlertNotificationChannel>('/alerts/notification-channels', channel)
  }

  /**
   * Update notification channel
   */
  async updateNotificationChannel(channelId: string, updates: Partial<AlertNotificationChannel>): Promise<AlertNotificationChannel> {
    return apiClient.patch<AlertNotificationChannel>(`/alerts/notification-channels/${channelId}`, updates)
  }

  /**
   * Delete notification channel
   */
  async deleteNotificationChannel(channelId: string): Promise<void> {
    return apiClient.delete(`/alerts/notification-channels/${channelId}`)
  }

  /**
   * Get notification rules
   */
  async getNotificationRules(): Promise<AlertNotificationRule[]> {
    return apiClient.get<AlertNotificationRule[]>('/alerts/notification-rules')
  }

  /**
   * Create notification rule
   */
  async createNotificationRule(rule: Omit<AlertNotificationRule, 'id' | 'createdAt' | 'updatedAt'>): Promise<AlertNotificationRule> {
    return apiClient.post<AlertNotificationRule>('/alerts/notification-rules', rule)
  }

  /**
   * Update notification rule
   */
  async updateNotificationRule(ruleId: string, updates: Partial<AlertNotificationRule>): Promise<AlertNotificationRule> {
    return apiClient.patch<AlertNotificationRule>(`/alerts/notification-rules/${ruleId}`, updates)
  }

  /**
   * Delete notification rule
   */
  async deleteNotificationRule(ruleId: string): Promise<void> {
    return apiClient.delete(`/alerts/notification-rules/${ruleId}`)
  }

  /**
   * Test notification channel
   */
  async testNotificationChannel(channelId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.post<{ success: boolean; message: string }>(`/alerts/notification-channels/${channelId}/test`)
  }
}

// Default service instance
export const alertService = new AlertService()