/**
 * Tests for token storage utilities
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { TokenStorage } from '../token-storage'
import type { TokenInfo } from '../types'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

describe('TokenStorage', () => {
  let tokenStorage: TokenStorage
  const mockTokens: TokenInfo = {
    accessToken: 'access-token-123',
    refreshToken: 'refresh-token-123',
    idToken: 'id-token-123',
    expiresIn: 3600,
    refreshExpiresIn: 7200,
    tokenType: 'Bearer'
  }

  beforeEach(() => {
    tokenStorage = TokenStorage.getInstance()
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('setTokens', () => {
    it('should store tokens in localStorage', () => {
      tokenStorage.setTokens(mockTokens)

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'observastack_tokens',
        expect.stringContaining('"accessToken":"access-token-123"')
      )
    })

    it('should handle localStorage errors gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      expect(() => tokenStorage.setTokens(mockTokens)).not.toThrow()
      expect(consoleSpy).toHaveBeenCalledWith('Failed to store tokens:', expect.any(Error))
      
      consoleSpy.mockRestore()
    })
  })

  describe('getTokens', () => {
    it('should retrieve valid tokens from localStorage', () => {
      const storedData = {
        ...mockTokens,
        storedAt: Date.now()
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(storedData))

      const tokens = tokenStorage.getTokens()

      expect(tokens).toEqual(expect.objectContaining({
        accessToken: 'access-token-123',
        refreshToken: 'refresh-token-123',
        tokenType: 'Bearer'
      }))
    })

    it('should return null for expired tokens', () => {
      const expiredData = {
        ...mockTokens,
        storedAt: Date.now() - 4000 * 1000 // 4000 seconds ago
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(expiredData))

      const tokens = tokenStorage.getTokens()

      expect(tokens).toBeNull()
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('observastack_tokens')
    })

    it('should return null when no tokens stored', () => {
      localStorageMock.getItem.mockReturnValue(null)

      const tokens = tokenStorage.getTokens()

      expect(tokens).toBeNull()
    })

    it('should handle JSON parse errors', () => {
      localStorageMock.getItem.mockReturnValue('invalid-json')
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const tokens = tokenStorage.getTokens()

      expect(tokens).toBeNull()
      expect(consoleSpy).toHaveBeenCalledWith('Failed to retrieve tokens:', expect.any(Error))
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('observastack_tokens')
      
      consoleSpy.mockRestore()
    })
  })

  describe('clearTokens', () => {
    it('should remove tokens from localStorage', () => {
      tokenStorage.clearTokens()

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('observastack_tokens')
    })
  })

  describe('hasValidTokens', () => {
    it('should return true for valid tokens', () => {
      const validData = {
        ...mockTokens,
        storedAt: Date.now()
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(validData))

      expect(tokenStorage.hasValidTokens()).toBe(true)
    })

    it('should return false for tokens expiring soon', () => {
      const soonToExpireData = {
        ...mockTokens,
        expiresIn: 30, // 30 seconds
        storedAt: Date.now()
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(soonToExpireData))

      expect(tokenStorage.hasValidTokens()).toBe(false)
    })

    it('should return false when no tokens exist', () => {
      localStorageMock.getItem.mockReturnValue(null)

      expect(tokenStorage.hasValidTokens()).toBe(false)
    })
  })

  describe('getAccessToken', () => {
    it('should return access token when valid', () => {
      const validData = {
        ...mockTokens,
        storedAt: Date.now()
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(validData))

      expect(tokenStorage.getAccessToken()).toBe('access-token-123')
    })

    it('should return null when tokens are invalid', () => {
      localStorageMock.getItem.mockReturnValue(null)

      expect(tokenStorage.getAccessToken()).toBeNull()
    })
  })

  describe('needsRefresh', () => {
    it('should return true when token expires soon', () => {
      const soonToExpireData = {
        ...mockTokens,
        expiresIn: 30, // 30 seconds
        storedAt: Date.now()
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(soonToExpireData))

      expect(tokenStorage.needsRefresh()).toBe(true)
    })

    it('should return false when token has plenty of time', () => {
      const validData = {
        ...mockTokens,
        storedAt: Date.now()
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(validData))

      expect(tokenStorage.needsRefresh()).toBe(false)
    })
  })

  describe('getTimeUntilExpiry', () => {
    it('should return correct time until expiry', () => {
      const validData = {
        ...mockTokens,
        expiresIn: 1800, // 30 minutes
        storedAt: Date.now()
      }
      localStorageMock.getItem.mockReturnValue(JSON.stringify(validData))

      expect(tokenStorage.getTimeUntilExpiry()).toBe(1800)
    })

    it('should return 0 when no tokens exist', () => {
      localStorageMock.getItem.mockReturnValue(null)

      expect(tokenStorage.getTimeUntilExpiry()).toBe(0)
    })
  })
})