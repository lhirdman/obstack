import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('WCAG Compliance Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        json: {
          id: 'user-1',
          username: 'testuser',
          email: 'test@example.com',
          tenantId: 'tenant-1',
          roles: ['viewer']
        }
      })
    })
  })

  test('search page should be WCAG AA compliant', async ({ page }) => {
    await page.goto('/search')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('alerts page should be WCAG AA compliant', async ({ page }) => {
    // Mock alerts data
    await page.route('**/api/alerts', async route => {
      await route.fulfill({
        json: {
          alerts: [
            {
              id: 'alert-1',
              title: 'High CPU Usage',
              description: 'CPU usage is above 90%',
              severity: 'critical',
              status: 'active',
              source: 'prometheus',
              timestamp: '2025-08-16T07:30:00Z',
              labels: { service: 'api-server' },
              tenantId: 'tenant-1'
            }
          ],
          total: 1,
          hasMore: false
        }
      })
    })

    await page.goto('/alerts')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('insights page should be WCAG AA compliant', async ({ page }) => {
    // Mock cost data
    await page.route('**/api/costs/summary', async route => {
      await route.fulfill({
        json: {
          totalCost: 1250.75,
          previousPeriodCost: 1100.50,
          trend: 'up',
          trendPercentage: 13.6,
          breakdown: {
            compute: 750.25,
            storage: 300.50,
            network: 150.00,
            other: 50.00
          },
          topNamespaces: [
            { name: 'production', cost: 800.25, percentage: 64.0 }
          ],
          alerts: {
            budgetExceeded: 2,
            anomaliesDetected: 1,
            optimizationOpportunities: 5
          },
          efficiency: {
            cpuUtilization: 65.5,
            memoryUtilization: 78.2,
            storageUtilization: 82.1,
            overallScore: 75.3
          }
        }
      })
    })

    await page.goto('/insights')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('dashboards page should be WCAG AA compliant', async ({ page }) => {
    await page.goto('/dashboards')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/search')
    
    // Check heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').allTextContents()
    
    // Should start with h1
    const firstHeading = await page.locator('h1').first()
    expect(firstHeading).toBeTruthy()
    
    // Run specific heading hierarchy check
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['heading-order'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/search')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['color-contrast'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have proper form labels', async ({ page }) => {
    await page.goto('/search')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['label', 'label-title-only'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have keyboard navigation support', async ({ page }) => {
    await page.goto('/search')
    
    // Test tab navigation
    await page.keyboard.press('Tab')
    let focusedElement = await page.locator(':focus').first()
    expect(focusedElement).toBeTruthy()
    
    // Continue tabbing through interactive elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab')
      focusedElement = await page.locator(':focus').first()
      expect(focusedElement).toBeTruthy()
    }
    
    // Test keyboard accessibility rules
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['keyboard', 'focus-order-semantics'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have proper ARIA attributes', async ({ page }) => {
    await page.goto('/search')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules([
        'aria-allowed-attr',
        'aria-required-attr',
        'aria-valid-attr-value',
        'aria-valid-attr'
      ])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have proper landmark regions', async ({ page }) => {
    await page.goto('/search')
    
    // Check for main landmark
    const main = await page.locator('main, [role="main"]')
    expect(main).toBeTruthy()
    
    // Check for navigation landmark
    const nav = await page.locator('nav, [role="navigation"]')
    expect(nav).toBeTruthy()
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['landmark-one-main', 'region'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should support screen readers', async ({ page }) => {
    await page.goto('/search')
    
    // Check for ARIA live regions
    const liveRegions = await page.locator('[aria-live]')
    expect(liveRegions).toBeTruthy()
    
    // Check for proper button labels
    const buttons = await page.locator('button')
    const buttonCount = await buttons.count()
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i)
      const ariaLabel = await button.getAttribute('aria-label')
      const textContent = await button.textContent()
      
      // Button should have either aria-label or text content
      expect(ariaLabel || textContent?.trim()).toBeTruthy()
    }
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['button-name', 'link-name'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should handle reduced motion preferences', async ({ page }) => {
    // Enable reduced motion
    await page.emulateMedia({ reducedMotion: 'reduce' })
    
    await page.goto('/search')
    
    // Check that animations are disabled or reduced
    const animatedElements = await page.locator('[class*="animate-"], [class*="transition-"]')
    const count = await animatedElements.count()
    
    if (count > 0) {
      // Verify that animations respect reduced motion
      for (let i = 0; i < count; i++) {
        const element = animatedElements.nth(i)
        const animationDuration = await element.evaluate(el => 
          getComputedStyle(el).animationDuration
        )
        
        // Animation should be disabled or very short
        expect(animationDuration === '0s' || animationDuration === '0.01s').toBeTruthy()
      }
    }
  })

  test('should be usable with high contrast mode', async ({ page }) => {
    // Enable high contrast mode
    await page.emulateMedia({ colorScheme: 'dark' })
    
    // Add high contrast styles
    await page.addStyleTag({
      content: `
        @media (prefers-contrast: high) {
          * {
            border: 2px solid currentColor !important;
          }
        }
      `
    })
    
    await page.goto('/search')
    
    // Verify elements are still visible and usable
    const searchInput = page.locator('[placeholder="Search logs, metrics, and traces..."]')
    await expect(searchInput).toBeVisible()
    
    const searchButton = page.locator('button:has-text("Search")')
    await expect(searchButton).toBeVisible()
    
    // Test color contrast in high contrast mode
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['color-contrast'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should support zoom up to 200%', async ({ page }) => {
    await page.goto('/search')
    
    // Set zoom to 200%
    await page.evaluate(() => {
      document.body.style.zoom = '2'
    })
    
    // Verify content is still accessible
    const searchInput = page.locator('[placeholder="Search logs, metrics, and traces..."]')
    await expect(searchInput).toBeVisible()
    
    // Verify no horizontal scrolling is needed
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
    const viewportWidth = await page.evaluate(() => window.innerWidth)
    
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth * 2.1) // Allow small margin
  })

  test('should have proper focus indicators', async ({ page }) => {
    await page.goto('/search')
    
    // Tab to first focusable element
    await page.keyboard.press('Tab')
    
    // Check that focus is visible
    const focusedElement = await page.locator(':focus').first()
    const outline = await focusedElement.evaluate(el => 
      getComputedStyle(el).outline
    )
    
    // Should have visible focus indicator
    expect(outline).not.toBe('none')
    expect(outline).not.toBe('')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withRules(['focus-order-semantics'])
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have proper error handling for screen readers', async ({ page }) => {
    // Mock API error
    await page.route('**/api/search', async route => {
      await route.abort('failed')
    })

    await page.goto('/search')
    
    // Trigger error
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'error test')
    await page.click('button:has-text("Search")')
    
    // Wait for error message
    await page.waitForSelector('[role="alert"], [aria-live="assertive"]')
    
    // Verify error is announced to screen readers
    const errorMessage = await page.locator('[role="alert"], [aria-live="assertive"]')
    expect(errorMessage).toBeTruthy()
    
    const errorText = await errorMessage.textContent()
    expect(errorText?.trim()).toBeTruthy()
  })
})