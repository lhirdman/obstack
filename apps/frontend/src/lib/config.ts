/**
 * Configuration service for the frontend application.
 * Handles environment variables and application settings.
 */

export interface KeycloakConfig {
  url: string;
  realm: string;
  clientId: string;
}

export interface AppConfig {
  authMethod: 'local' | 'keycloak';
  keycloak?: KeycloakConfig;
  apiBaseUrl: string;
}

class ConfigService {
  private config: AppConfig;

  constructor() {
    this.config = this.loadConfig();
  }

  private loadConfig(): AppConfig {
    // Default configuration
    const config: AppConfig = {
      authMethod: (import.meta.env.VITE_AUTH_METHOD as 'local' | 'keycloak') || 'local',
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api/v1',
    };

    // Load Keycloak configuration if auth method is keycloak
    if (config.authMethod === 'keycloak') {
      config.keycloak = {
        url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
        realm: import.meta.env.VITE_KEYCLOAK_REALM || 'observastack',
        clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'observastack-frontend',
      };
    }

    return config;
  }

  getConfig(): AppConfig {
    return this.config;
  }

  getAuthMethod(): 'local' | 'keycloak' {
    return this.config.authMethod;
  }

  getKeycloakConfig(): KeycloakConfig | undefined {
    return this.config.keycloak;
  }

  getApiBaseUrl(): string {
    return this.config.apiBaseUrl;
  }
}

// Export a default instance
export const configService = new ConfigService();

// Export the class for custom instances
export default ConfigService;