"""
Tests for configuration system.
"""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings, AuthMethod


class TestSettings:
    """Test cases for Settings configuration."""

    def test_default_settings(self):
        """Test default configuration values."""
        with patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            
            assert settings.auth_method == AuthMethod.LOCAL
            assert settings.jwt_algorithm == "HS256"
            assert settings.access_token_expire_minutes == 30
            assert settings.environment == "development"

    def test_local_auth_development_default_secret(self):
        """Test that development environment gets default JWT secret."""
        with patch.dict('os.environ', {'ENVIRONMENT': 'development'}, clear=True):
            settings = Settings()
            
            assert settings.auth_method == AuthMethod.LOCAL
            assert settings.jwt_secret_key == "dev-secret-key-not-for-production-use"

    def test_local_auth_production_requires_secret(self):
        """Test that production environment requires JWT secret."""
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}, clear=True):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY environment variable is required"):
                Settings()

    def test_local_auth_with_custom_secret(self):
        """Test local auth with custom JWT secret."""
        env_vars = {
            'AUTH_METHOD': 'local',
            'JWT_SECRET_KEY': 'custom-secret-key',
            'ENVIRONMENT': 'production'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            settings = Settings()
            
            assert settings.auth_method == AuthMethod.LOCAL
            assert settings.jwt_secret_key == 'custom-secret-key'

    def test_keycloak_auth_requires_config(self):
        """Test that Keycloak auth requires all necessary configuration."""
        env_vars = {
            'AUTH_METHOD': 'keycloak'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            with pytest.raises(ValueError, match="The following environment variables are required"):
                Settings()

    def test_keycloak_auth_missing_server_url(self):
        """Test Keycloak auth validation with missing server URL."""
        env_vars = {
            'AUTH_METHOD': 'keycloak',
            'KEYCLOAK_REALM': 'test-realm',
            'KEYCLOAK_CLIENT_ID': 'test-client'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            with pytest.raises(ValueError, match="KEYCLOAK_SERVER_URL"):
                Settings()

    def test_keycloak_auth_missing_realm(self):
        """Test Keycloak auth validation with missing realm."""
        env_vars = {
            'AUTH_METHOD': 'keycloak',
            'KEYCLOAK_SERVER_URL': 'https://keycloak.example.com',
            'KEYCLOAK_CLIENT_ID': 'test-client'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            with pytest.raises(ValueError, match="KEYCLOAK_REALM"):
                Settings()

    def test_keycloak_auth_missing_client_id(self):
        """Test Keycloak auth validation with missing client ID."""
        env_vars = {
            'AUTH_METHOD': 'keycloak',
            'KEYCLOAK_SERVER_URL': 'https://keycloak.example.com',
            'KEYCLOAK_REALM': 'test-realm'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            with pytest.raises(ValueError, match="KEYCLOAK_CLIENT_ID"):
                Settings()

    def test_keycloak_auth_complete_config(self):
        """Test Keycloak auth with complete configuration."""
        env_vars = {
            'AUTH_METHOD': 'keycloak',
            'KEYCLOAK_SERVER_URL': 'https://keycloak.example.com',
            'KEYCLOAK_REALM': 'test-realm',
            'KEYCLOAK_CLIENT_ID': 'test-client',
            'KEYCLOAK_CLIENT_SECRET': 'test-secret'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            settings = Settings()
            
            assert settings.auth_method == AuthMethod.KEYCLOAK
            assert settings.keycloak_server_url == 'https://keycloak.example.com'
            assert settings.keycloak_realm == 'test-realm'
            assert settings.keycloak_client_id == 'test-client'
            assert settings.keycloak_client_secret == 'test-secret'

    def test_keycloak_auth_without_client_secret(self):
        """Test Keycloak auth without client secret (public client)."""
        env_vars = {
            'AUTH_METHOD': 'keycloak',
            'KEYCLOAK_SERVER_URL': 'https://keycloak.example.com',
            'KEYCLOAK_REALM': 'test-realm',
            'KEYCLOAK_CLIENT_ID': 'test-client'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            settings = Settings()
            
            assert settings.auth_method == AuthMethod.KEYCLOAK
            assert settings.keycloak_client_secret is None

    def test_custom_token_expiration(self):
        """Test custom token expiration configuration."""
        env_vars = {
            'ACCESS_TOKEN_EXPIRE_MINUTES': '60',
            'JWT_SECRET_KEY': 'test-secret'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            settings = Settings()
            
            assert settings.access_token_expire_minutes == 60

    def test_custom_jwt_algorithm(self):
        """Test custom JWT algorithm configuration."""
        env_vars = {
            'JWT_ALGORITHM': 'HS512',
            'JWT_SECRET_KEY': 'test-secret'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            settings = Settings()
            
            assert settings.jwt_algorithm == 'HS512'

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive."""
        env_vars = {
            'auth_method': 'keycloak',  # lowercase
            'keycloak_server_url': 'https://keycloak.example.com',
            'keycloak_realm': 'test-realm',
            'keycloak_client_id': 'test-client'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            settings = Settings()
            
            assert settings.auth_method == AuthMethod.KEYCLOAK

    def test_invalid_auth_method(self):
        """Test validation with invalid auth method."""
        env_vars = {
            'AUTH_METHOD': 'invalid-method'
        }
        
        with patch.dict('os.environ', env_vars, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_environment_specific_validation(self):
        """Test that validation behaves differently based on environment."""
        # Development should work without JWT_SECRET_KEY
        with patch.dict('os.environ', {'ENVIRONMENT': 'development'}, clear=True):
            settings = Settings()
            assert settings.jwt_secret_key == "dev-secret-key-not-for-production-use"
        
        # Production should require JWT_SECRET_KEY
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}, clear=True):
            with pytest.raises(ValueError):
                Settings()
        
        # Staging should require JWT_SECRET_KEY
        with patch.dict('os.environ', {'ENVIRONMENT': 'staging'}, clear=True):
            with pytest.raises(ValueError):
                Settings()


class TestAuthMethod:
    """Test cases for AuthMethod enum."""

    def test_auth_method_values(self):
        """Test AuthMethod enum values."""
        assert AuthMethod.LOCAL == "local"
        assert AuthMethod.KEYCLOAK == "keycloak"

    def test_auth_method_from_string(self):
        """Test creating AuthMethod from string."""
        assert AuthMethod("local") == AuthMethod.LOCAL
        assert AuthMethod("keycloak") == AuthMethod.KEYCLOAK

    def test_invalid_auth_method_string(self):
        """Test invalid AuthMethod string raises error."""
        with pytest.raises(ValueError):
            AuthMethod("invalid")