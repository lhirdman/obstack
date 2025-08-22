import { test, expect } from '@playwright/test';

test.describe('Keycloak Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Set environment variables for Keycloak auth
    await page.addInitScript(() => {
      window.localStorage.setItem('VITE_AUTH_METHOD', 'keycloak');
      window.localStorage.setItem('VITE_KEYCLOAK_URL', 'http://localhost:8080');
      window.localStorage.setItem('VITE_KEYCLOAK_REALM', 'observastack');
      window.localStorage.setItem('VITE_KEYCLOAK_CLIENT_ID', 'observastack-frontend');
    });
  });

  test('should redirect to Keycloak login when AUTH_METHOD is keycloak', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');

    // Should see the Keycloak login button instead of email/password form
    await expect(page.getByText('Sign in with your corporate credentials')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In with SSO' })).toBeVisible();

    // Should not see local login form elements
    await expect(page.getByLabel('Email Address')).not.toBeVisible();
    await expect(page.getByLabel('Password')).not.toBeVisible();
    await expect(page.getByText("Don't have an account? Sign up")).not.toBeVisible();
  });

  test('should initiate Keycloak login flow when SSO button is clicked', async ({ page, context }) => {
    // Navigate to the application
    await page.goto('/');

    // Wait for the SSO button to be visible
    const ssoButton = page.getByRole('button', { name: 'Sign In with SSO' });
    await expect(ssoButton).toBeVisible();

    // Set up a promise to wait for the new page (Keycloak login)
    const pagePromise = context.waitForEvent('page');

    // Click the SSO button
    await ssoButton.click();

    // Wait for the new page to open (Keycloak login page)
    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    // Verify we're redirected to Keycloak
    expect(newPage.url()).toContain('localhost:8080');
    expect(newPage.url()).toContain('/auth/realms/observastack');
    expect(newPage.url()).toContain('client_id=observastack-frontend');
    expect(newPage.url()).toContain('redirect_uri=');
    expect(newPage.url()).toContain('/auth/callback');
  });

  test('should handle successful Keycloak authentication callback', async ({ page }) => {
    // Mock a successful Keycloak callback by navigating directly to callback URL
    // with mock authentication parameters
    const mockCallbackUrl = '/auth/callback#state=test-state&session_state=test-session&code=test-code';
    
    // Mock Keycloak initialization to return authenticated state
    await page.addInitScript(() => {
      // Mock the Keycloak library
      (window as any).Keycloak = class MockKeycloak {
        init() {
          return Promise.resolve(true);
        }
        
        get authenticated() {
          return true;
        }
        
        get token() {
          return 'mock-jwt-token';
        }
        
        get tokenParsed() {
          return {
            sub: 'user-123',
            preferred_username: 'testuser',
            email: 'test@example.com',
            realm_access: { roles: ['user'] }
          };
        }
        
        get profile() {
          return {
            id: 'user-123',
            username: 'testuser',
            email: 'test@example.com',
            firstName: 'Test',
            lastName: 'User'
          };
        }
        
        loadUserProfile() {
          return Promise.resolve();
        }
        
        updateToken() {
          return Promise.resolve(false);
        }
      };
    });

    // Navigate to the callback URL
    await page.goto(mockCallbackUrl);

    // Should show the callback processing UI initially
    await expect(page.getByText('Completing Sign In...')).toBeVisible();
    
    // Wait for authentication to complete and redirect to dashboard
    await page.waitForURL('/', { timeout: 10000 });
    
    // Should now be on the main dashboard
    await expect(page.getByText('ObservaStack')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
  });

  test('should handle Keycloak authentication failure', async ({ page }) => {
    // Mock a failed Keycloak callback
    await page.addInitScript(() => {
      (window as any).Keycloak = class MockKeycloak {
        init() {
          return Promise.reject(new Error('Authentication failed'));
        }
      };
    });

    // Navigate to the callback URL
    await page.goto('/auth/callback');

    // Should show error message
    await expect(page.getByText('Authentication Failed')).toBeVisible();
    await expect(page.getByText('Authentication failed')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Return to Login' })).toBeVisible();
  });

  test('should allow user to access protected routes after Keycloak authentication', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      (window as any).Keycloak = class MockKeycloak {
        init() {
          return Promise.resolve(true);
        }
        
        get authenticated() {
          return true;
        }
        
        get token() {
          return 'mock-jwt-token';
        }
        
        get tokenParsed() {
          return {
            sub: 'user-123',
            preferred_username: 'testuser',
            email: 'test@example.com',
            realm_access: { roles: ['user'] }
          };
        }
        
        get profile() {
          return {
            id: 'user-123',
            username: 'testuser',
            email: 'test@example.com'
          };
        }
        
        loadUserProfile() {
          return Promise.resolve();
        }
      };
    });

    // Navigate to the application
    await page.goto('/');

    // Should be able to access the dashboard (protected route)
    await expect(page.getByText('ObservaStack')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
    
    // Should not see login form
    await expect(page.getByRole('button', { name: 'Sign In with SSO' })).not.toBeVisible();
  });

  test('should logout from Keycloak when logout button is clicked', async ({ page, context }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      (window as any).Keycloak = class MockKeycloak {
        init() {
          return Promise.resolve(true);
        }
        
        get authenticated() {
          return true;
        }
        
        logout() {
          // Mock logout redirect
          window.location.href = 'http://localhost:8080/auth/realms/observastack/protocol/openid-connect/logout';
          return Promise.resolve();
        }
        
        get token() {
          return 'mock-jwt-token';
        }
        
        get profile() {
          return {
            id: 'user-123',
            username: 'testuser',
            email: 'test@example.com'
          };
        }
        
        loadUserProfile() {
          return Promise.resolve();
        }
      };
    });

    // Navigate to the application
    await page.goto('/');

    // Should be authenticated and see logout button
    const logoutButton = page.getByRole('button', { name: 'Logout' });
    await expect(logoutButton).toBeVisible();

    // Set up a promise to wait for navigation
    const navigationPromise = page.waitForURL(/localhost:8080.*logout/);

    // Click logout
    await logoutButton.click();

    // Should redirect to Keycloak logout
    await navigationPromise;
    expect(page.url()).toContain('localhost:8080');
    expect(page.url()).toContain('logout');
  });
});