/**
 * Token storage utilities with automatic refresh
 */

import type { TokenInfo } from './types'

const TOKEN_STORAGE_KEY = 'observastack_tokens'
const TOKEN_REFRESH_THRESHOLD = 60 // Refresh if token expires in less than 60 seconds

export class TokenStorage {
  private static instance: TokenStorage
  private refreshTimer: number | null = null
  private onTokenRefresh?: (tokens: TokenInfo) => void
  private onTokenExpired?: () => void

  private constructor() {}

  static getInstance(): TokenStorage {
    if (!TokenStorage.instance) {
      TokenStorage.instance = new TokenStorage()
    }
    return TokenStorage.instance
  }

  /**
   * Store tokens in localStorage with automatic refresh scheduling
   */
  setTokens(tokens: TokenInfo): void {
    try {
      const tokenData = {
        ...tokens,
        storedAt: Date.now()
      }
      localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokenData))
      this.scheduleTokenRefresh(tokens.expiresIn)
    } catch (error) {
      console.error('Failed to store tokens:', error)
    }
  }

  /**
   * Retrieve tokens from localStorage
   */
  getTokens(): TokenInfo | null {
    try {
      const stored = localStorage.getItem(TOKEN_STORAGE_KEY)
      if (!stored) return null

      const tokenData = JSON.parse(stored)
      const now = Date.now()
      const storedAt = tokenData.storedAt || now
      const ageInSeconds = Math.floor((now - storedAt) / 1000)

      // Check if access token is expired
      if (ageInSeconds >= tokenData.expiresIn) {
        this.clearTokens()
        return null
      }

      return {
        accessToken: tokenData.accessToken,
        refreshToken: tokenData.refreshToken,
        idToken: tokenData.idToken,
        expiresIn: tokenData.expiresIn - ageInSeconds,
        refreshExpiresIn: tokenData.refreshExpiresIn - ageInSeconds,
        tokenType: tokenData.tokenType || 'Bearer'
      }
    } catch (error) {
      console.error('Failed to retrieve tokens:', error)
      this.clearTokens()
      return null
    }
  }

  /**
   * Clear stored tokens
   */
  clearTokens(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    this.clearRefreshTimer()
  }

  /**
   * Check if tokens are available and valid
   */
  hasValidTokens(): boolean {
    const tokens = this.getTokens()
    return tokens !== null && tokens.expiresIn > TOKEN_REFRESH_THRESHOLD
  }

  /**
   * Get access token if available and valid
   */
  getAccessToken(): string | null {
    const tokens = this.getTokens()
    return tokens?.accessToken || null
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(expiresIn: number): void {
    this.clearRefreshTimer()

    // Schedule refresh before token expires
    const refreshIn = Math.max(0, (expiresIn - TOKEN_REFRESH_THRESHOLD) * 1000)
    
    this.refreshTimer = window.setTimeout(() => {
      if (this.onTokenRefresh) {
        const tokens = this.getTokens()
        if (tokens) {
          this.onTokenRefresh(tokens)
        }
      }
    }, refreshIn)
  }

  /**
   * Clear the refresh timer
   */
  private clearRefreshTimer(): void {
    if (this.refreshTimer) {
      window.clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }
  }

  /**
   * Set callback for token refresh
   */
  onTokenRefreshNeeded(callback: (tokens: TokenInfo) => void): void {
    this.onTokenRefresh = callback
  }

  /**
   * Set callback for token expiration
   */
  onTokenExpiration(callback: () => void): void {
    this.onTokenExpired = callback
  }

  /**
   * Check if token needs refresh
   */
  needsRefresh(): boolean {
    const tokens = this.getTokens()
    return tokens !== null && tokens.expiresIn <= TOKEN_REFRESH_THRESHOLD
  }

  /**
   * Get time until token expires (in seconds)
   */
  getTimeUntilExpiry(): number {
    const tokens = this.getTokens()
    return tokens?.expiresIn || 0
  }
}