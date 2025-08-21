"""
Tests for Keycloak service integration.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from jose import jwt
import requests

from app.services.keycloak_service import KeycloakService
from app.core.config import settings


@pytest.fixture
def keycloak_service():
    """Create a fresh KeycloakService instance for testing."""
    service = KeycloakService()
    service.clear_cache()  # Ensure clean state
    return service


@pytest.fixture
def mock_keycloak_settings():
    """Mock Keycloak settings for testing."""
    with patch.object(settings, 'keycloak_server_url', 'https://keycloak.example.com'):
        with patch.object(settings, 'keycloak_realm', 'test-realm'):
            with patch.object(settings, 'keycloak_client_id', 'test-client'):
                yield


@pytest.fixture
def sample_jwks():
    """Sample JWKS response from Keycloak."""
    return {
        "keys": [
            {
                "kid": "test-key-id",
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "n": "sample-modulus",
                "e": "AQAB"
            }
        ]
    }


@pytest.fixture
def sample_realm_info():
    """Sample realm info response from Keycloak."""
    return {
        "realm": "test-realm",
        "issuer": "https://keycloak.example.com/realms/test-realm",
        "auth_endpoint": "https://keycloak.example.com/realms/test-realm/protocol/openid_connect/auth"
    }


@pytest.fixture
def sample_jwt_payload():
    """Sample JWT payload from Keycloak."""
    return {
        "sub": "user-123",
        "preferred_username": "testuser",
        "email": "test@example.com",
        "given_name": "Test",
        "family_name": "User",
        "name": "Test User",
        "email_verified": True,
        "realm_access": {
            "roles": ["user", "manager"]
        },
        "resource_access": {
            "test-client": {
                "roles": ["client-admin"]
            }
        },
        "tenant": "test-org",
        "iss": "https://keycloak.example.com/realms/test-realm",
        "aud": "test-client",
        "exp": 9999999999,  # Far future
        "iat": 1000000000,
        "nbf": 1000000000
    }


class TestKeycloakService:
    """Test cases for KeycloakService."""

    def test_realm_url_property(self, keycloak_service, mock_keycloak_settings):
        """Test realm URL property construction."""
        expected_url = "https://keycloak.example.com/realms/test-realm"
        assert keycloak_service.realm_url == expected_url

    def test_jwks_uri_property(self, keycloak_service, mock_keycloak_settings):
        """Test JWKS URI property construction."""
        expected_uri = "https://keycloak.example.com/realms/test-realm/protocol/openid_connect/certs"
        assert keycloak_service.jwks_uri == expected_uri

    @patch('requests.get')
    def test_get_realm_info_success(self, mock_get, keycloak_service, mock_keycloak_settings, sample_realm_info):
        """Test successful realm info retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = sample_realm_info
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = keycloak_service.get_realm_info()

        assert result == sample_realm_info
        mock_get.assert_called_once_with(
            "https://keycloak.example.com/realms/test-realm",
            timeout=10
        )

    @patch('requests.get')
    def test_get_realm_info_caching(self, mock_get, keycloak_service, mock_keycloak_settings, sample_realm_info):
        """Test that realm info is cached after first request."""
        mock_response = Mock()
        mock_response.json.return_value = sample_realm_info
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # First call
        result1 = keycloak_service.get_realm_info()
        # Second call
        result2 = keycloak_service.get_realm_info()

        assert result1 == result2 == sample_realm_info
        # Should only make one HTTP request due to caching
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_realm_info_failure(self, mock_get, keycloak_service, mock_keycloak_settings):
        """Test realm info retrieval failure."""
        mock_get.side_effect = requests.RequestException("Connection failed")

        with pytest.raises(requests.RequestException):
            keycloak_service.get_realm_info()

    @patch('requests.get')
    def test_get_jwks_success(self, mock_get, keycloak_service, mock_keycloak_settings, sample_jwks):
        """Test successful JWKS retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = sample_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = keycloak_service.get_jwks()

        assert result == sample_jwks
        mock_get.assert_called_once_with(
            "https://keycloak.example.com/realms/test-realm/protocol/openid_connect/certs",
            timeout=10
        )

    @patch('requests.get')
    def test_get_jwks_caching(self, mock_get, keycloak_service, mock_keycloak_settings, sample_jwks):
        """Test that JWKS is cached after first request."""
        mock_response = Mock()
        mock_response.json.return_value = sample_jwks
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # First call
        result1 = keycloak_service.get_jwks()
        # Second call
        result2 = keycloak_service.get_jwks()

        assert result1 == result2 == sample_jwks
        # Should only make one HTTP request due to caching
        mock_get.assert_called_once()

    def test_extract_user_info(self, keycloak_service, sample_jwt_payload):
        """Test user information extraction from JWT payload."""
        result = keycloak_service.extract_user_info(sample_jwt_payload)

        expected = {
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "full_name": "Test User",
            "email_verified": True,
        }
        assert result == expected

    def test_extract_roles(self, keycloak_service, sample_jwt_payload):
        """Test role extraction from JWT payload."""
        result = keycloak_service.extract_roles(sample_jwt_payload)

        expected_roles = ["user", "manager", "client:client-admin"]
        assert set(result) == set(expected_roles)

    def test_extract_roles_filters_system_roles(self, keycloak_service):
        """Test that system roles are filtered out."""
        payload = {
            "realm_access": {
                "roles": ["user", "offline_access", "uma_authorization", "default-roles-test"]
            },
            "resource_access": {}
        }

        result = keycloak_service.extract_roles(payload)

        # Should only contain 'user', system roles should be filtered
        assert result == ["user"]

    def test_extract_tenant_info_with_tenant_claim(self, keycloak_service, sample_jwt_payload):
        """Test tenant extraction when tenant claim is present."""
        result = keycloak_service.extract_tenant_info(sample_jwt_payload)
        assert result == "test-org"

    def test_extract_tenant_info_fallback_to_realm(self, keycloak_service, mock_keycloak_settings):
        """Test tenant extraction fallback to realm name."""
        payload = {}  # No tenant claims
        result = keycloak_service.extract_tenant_info(payload)
        assert result == "test-realm"

    def test_extract_tenant_info_alternative_claims(self, keycloak_service):
        """Test tenant extraction from alternative claim names."""
        test_cases = [
            ({"organization": "org1"}, "org1"),
            ({"org": "org2"}, "org2"),
            ({"company": "company1"}, "company1"),
            ({"tenant_id": "tenant1"}, "tenant1"),
            ({"org_id": "orgid1"}, "orgid1"),
        ]

        for payload, expected in test_cases:
            result = keycloak_service.extract_tenant_info(payload)
            assert result == expected

    def test_map_keycloak_roles_to_internal(self, keycloak_service):
        """Test mapping of Keycloak roles to internal roles."""
        keycloak_roles = ["admin", "manager", "user", "client:viewer", "unknown-role"]
        result = keycloak_service.map_keycloak_roles_to_internal(keycloak_roles)

        expected_roles = ["admin", "manager", "user", "viewer"]
        assert set(result) == set(expected_roles)

    def test_map_keycloak_roles_default_user_role(self, keycloak_service):
        """Test that 'user' role is assigned when no roles map."""
        keycloak_roles = ["unknown-role", "another-unknown"]
        result = keycloak_service.map_keycloak_roles_to_internal(keycloak_roles)

        assert result == ["user"]

    def test_clear_cache(self, keycloak_service):
        """Test cache clearing functionality."""
        # Set some cached data
        keycloak_service._jwks_cache = {"test": "data"}
        keycloak_service._realm_info_cache = {"test": "info"}

        keycloak_service.clear_cache()

        assert keycloak_service._jwks_cache is None
        assert keycloak_service._realm_info_cache is None

    @patch('app.services.keycloak_service.jwt.decode')
    @patch('app.services.keycloak_service.jwt.get_unverified_header')
    def test_validate_jwt_token_success(self, mock_get_header, mock_decode, keycloak_service, 
                                       mock_keycloak_settings, sample_jwks, sample_realm_info, sample_jwt_payload):
        """Test successful JWT token validation."""
        # Mock dependencies
        mock_get_header.return_value = {"kid": "test-key-id"}
        mock_decode.return_value = sample_jwt_payload
        
        with patch.object(keycloak_service, 'get_jwks', return_value=sample_jwks):
            with patch.object(keycloak_service, 'get_realm_info', return_value=sample_realm_info):
                result = keycloak_service.validate_jwt_token("test-token")

        assert result == sample_jwt_payload

    @patch('app.services.keycloak_service.jwt.get_unverified_header')
    def test_validate_jwt_token_missing_kid(self, mock_get_header, keycloak_service):
        """Test JWT validation failure when kid is missing."""
        mock_get_header.return_value = {}  # No kid

        result = keycloak_service.validate_jwt_token("test-token")

        assert result is None

    @patch('app.services.keycloak_service.jwt.get_unverified_header')
    def test_validate_jwt_token_key_not_found(self, mock_get_header, keycloak_service, 
                                             mock_keycloak_settings, sample_jwks):
        """Test JWT validation failure when key is not found in JWKS."""
        mock_get_header.return_value = {"kid": "unknown-key-id"}
        
        with patch.object(keycloak_service, 'get_jwks', return_value=sample_jwks):
            result = keycloak_service.validate_jwt_token("test-token")

        assert result is None

    @patch('app.services.keycloak_service.jwt.decode')
    @patch('app.services.keycloak_service.jwt.get_unverified_header')
    def test_validate_jwt_token_jwt_error(self, mock_get_header, mock_decode, keycloak_service,
                                         mock_keycloak_settings, sample_jwks, sample_realm_info):
        """Test JWT validation failure due to JWT error."""
        mock_get_header.return_value = {"kid": "test-key-id"}
        mock_decode.side_effect = jwt.JWTError("Invalid token")
        
        with patch.object(keycloak_service, 'get_jwks', return_value=sample_jwks):
            with patch.object(keycloak_service, 'get_realm_info', return_value=sample_realm_info):
                result = keycloak_service.validate_jwt_token("test-token")

        assert result is None