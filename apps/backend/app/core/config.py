"""
Configuration settings for the ObservaStack backend application.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class AuthMethod(str, Enum):
    """Supported authentication methods."""
    LOCAL = "local"
    KEYCLOAK = "keycloak"


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Authentication Configuration
    auth_method: AuthMethod = Field(
        default=AuthMethod.LOCAL,
        description="Authentication method to use (local or keycloak)"
    )
    
    # Local JWT Configuration
    jwt_secret_key: Optional[str] = Field(
        default=None,
        description="Secret key for JWT token signing (required for local auth)"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT token signing"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )
    
    # Keycloak Configuration
    keycloak_server_url: Optional[str] = Field(
        default=None,
        description="Keycloak server URL (required for keycloak auth)"
    )
    keycloak_realm: Optional[str] = Field(
        default=None,
        description="Keycloak realm name (required for keycloak auth)"
    )
    keycloak_client_id: Optional[str] = Field(
        default=None,
        description="Keycloak client ID (required for keycloak auth)"
    )
    keycloak_client_secret: Optional[str] = Field(
        default=None,
        description="Keycloak client secret (optional, for confidential clients)"
    )
    
    # Prometheus Configuration
    prometheus_url: str = Field(
        default="http://localhost:9090",
        description="Prometheus/Thanos API endpoint URL"
    )
    prometheus_timeout: int = Field(
        default=30,
        description="Timeout for Prometheus API requests in seconds"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_auth_config()
    
    def _validate_auth_config(self):
        """Validate authentication configuration based on selected method."""
        if self.auth_method == AuthMethod.LOCAL:
            if not self.jwt_secret_key:
                if self.environment == "development":
                    self.jwt_secret_key = "dev-secret-key-not-for-production-use"
                    print("WARNING: Using development JWT secret key. Set JWT_SECRET_KEY environment variable for production.")
                else:
                    raise ValueError("JWT_SECRET_KEY environment variable is required for local authentication in non-development environments")
        
        elif self.auth_method == AuthMethod.KEYCLOAK:
            missing_fields = []
            if not self.keycloak_server_url:
                missing_fields.append("KEYCLOAK_SERVER_URL")
            if not self.keycloak_realm:
                missing_fields.append("KEYCLOAK_REALM")
            if not self.keycloak_client_id:
                missing_fields.append("KEYCLOAK_CLIENT_ID")
            
            if missing_fields:
                raise ValueError(f"The following environment variables are required for Keycloak authentication: {', '.join(missing_fields)}")


# Global settings instance
settings = Settings()