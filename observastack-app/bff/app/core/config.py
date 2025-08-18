"""Configuration settings for ObservaStack BFF."""

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    app_name: str = Field(default="ObservaStack BFF", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API settings
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    # Authentication settings
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Keycloak settings
    keycloak_url: str = Field(default="http://localhost:8080", env="KEYCLOAK_URL")
    keycloak_realm: str = Field(default="observastack", env="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="observastack-bff", env="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: Optional[str] = Field(default=None, env="KEYCLOAK_CLIENT_SECRET")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./observastack.db", env="DATABASE_URL")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Observability service URLs
    prometheus_url: str = Field(default="http://localhost:9090", env="PROMETHEUS_URL")
    loki_url: str = Field(default="http://localhost:3100", env="LOKI_URL")
    tempo_url: str = Field(default="http://localhost:3200", env="TEMPO_URL")
    grafana_url: str = Field(default="http://localhost:3000", env="GRAFANA_URL")
    
    # OpenCost settings
    opencost_url: str = Field(default="http://localhost:9003", env="OPENCOST_URL")
    opencost_timeout: int = Field(default=30, env="OPENCOST_TIMEOUT")
    opencost_cache_ttl: int = Field(default=300, env="OPENCOST_CACHE_TTL")  # 5 minutes
    opencost_retry_attempts: int = Field(default=3, env="OPENCOST_RETRY_ATTEMPTS")
    opencost_retry_delay: float = Field(default=1.0, env="OPENCOST_RETRY_DELAY")
    
    # Cost monitoring settings
    cost_alert_check_interval: int = Field(default=300, env="COST_ALERT_CHECK_INTERVAL")  # 5 minutes
    cost_optimization_cache_ttl: int = Field(default=3600, env="COST_OPTIMIZATION_CACHE_TTL")  # 1 hour
    default_cost_currency: str = Field(default="USD", env="DEFAULT_COST_CURRENCY")
    min_cost_savings_threshold: float = Field(default=10.0, env="MIN_COST_SAVINGS_THRESHOLD")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Performance settings
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()