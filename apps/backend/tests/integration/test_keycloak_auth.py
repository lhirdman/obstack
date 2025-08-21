"""
Integration tests for Keycloak authentication flow.
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.config import settings, AuthMethod
from app.db.models import User, Tenant
from app.services.keycloak_service import keycloak_service


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_keycloak_config():
    """Mock Keycloak configuration."""
    with patch.object(settings, 'auth_method', AuthMethod.KEYCLOAK):
        with patch.object(settings, 'keycloak_server_url', 'https://keycloak.test.com'):
            with patch.object(settings, 'keycloak_realm', 'test-realm'):
                with patch.object(settings, 'keycloak_client_id', 'test-client'):
                    yield


@pytest.fixture
def sample_keycloak_token_payload():
    """Sample Keycloak token payload for testing."""
    return {
        "sub": "keycloak-user-123",
        "preferred_username": "john.doe",
        "email": "john.doe@example.com",
        "given_name": "John",
        "family_name": "Doe",
        "name": "John Doe",
        "email_verified": True,
        "realm_access": {
            "roles": ["user", "manager"]
        },
        "resource_access": {
            "test-client": {
                "roles": ["admin"]
            }
        },
        "tenant": "acme-corp",
        "iss": "https://keycloak.test.com/realms/test-realm",
        "aud": "test-client",
        "exp": 9999999999,
        "iat": 1000000000,
        "nbf": 1000000000
    }


class TestKeycloakAuthIntegration:
    """Integration tests for Keycloak authentication."""

    def test_auth_info_endpoint_keycloak_mode(self, client, mock_keycloak_config):
        """Test auth info endpoint returns Keycloak configuration."""
        response = client.get("/api/v1/auth/auth-info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["auth_method"] == "keycloak"
        assert data["supports_keycloak_auth"] is True
        assert data["supports_local_auth"] is False
        assert data["keycloak_server_url"] == "https://keycloak.test.com"
        assert data["keycloak_realm"] == "test-realm"
        assert data["keycloak_client_id"] == "test-client"
        assert "keycloak_auth_url" in data
        assert "keycloak_token_url" in data

    @patch('app.services.keycloak_service.keycloak_service.validate_jwt_token')
    def test_protected_endpoint_with_valid_keycloak_token(self, mock_validate, client, 
                                                         mock_keycloak_config, sample_keycloak_token_payload):
        """Test accessing protected endpoint with valid Keycloak token."""
        # Mock successful token validation
        mock_validate.return_value = sample_keycloak_token_payload
        
        # Mock database operations
        with patch('app.core.security.select') as mock_select:
            with patch('app.db.session.get_db') as mock_get_db:
                # Mock database session and user creation
                mock_db = Mock(spec=AsyncSession)
                mock_get_db.return_value = mock_db
                
                # Mock user lookup (user doesn't exist initially)
                mock_result = Mock()
                mock_result.scalar_one_or_none.return_value = None
                mock_db.execute.return_value = mock_result
                
                # Mock tenant creation
                mock_tenant = Tenant(id=1, name="acme-corp")
                mock_db.flush = Mock()
                mock_db.add = Mock()
                mock_db.commit = Mock()
                mock_db.refresh = Mock()
                
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer valid-keycloak-token"}
                )
                
                # Should create user and return success
                assert response.status_code == 200

    @patch('app.services.keycloak_service.keycloak_service.validate_jwt_token')
    def test_protected_endpoint_with_invalid_keycloak_token(self, mock_validate, client, mock_keycloak_config):
        """Test accessing protected endpoint with invalid Keycloak token."""
        # Mock failed token validation
        mock_validate.return_value = None
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_protected_endpoint_without_token_keycloak_mode(self, client, mock_keycloak_config):
        """Test accessing protected endpoint without token in Keycloak mode."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    @patch('app.services.keycloak_service.keycloak_service.validate_jwt_token')
    def test_user_creation_from_keycloak_token(self, mock_validate, client, 
                                              mock_keycloak_config, sample_keycloak_token_payload):
        """Test that users are created from Keycloak token information."""
        mock_validate.return_value = sample_keycloak_token_payload
        
        with patch('app.core.security.select') as mock_select:
            with patch('app.db.session.get_db') as mock_get_db:
                mock_db = Mock(spec=AsyncSession)
                mock_get_db.return_value = mock_db
                
                # Mock user doesn't exist
                mock_user_result = Mock()
                mock_user_result.scalar_one_or_none.return_value = None
                
                # Mock tenant doesn't exist
                mock_tenant_result = Mock()
                mock_tenant_result.scalar_one_or_none.return_value = None
                
                # Configure mock to return different results for different queries
                mock_db.execute.side_effect = [mock_user_result, mock_tenant_result]
                
                mock_db.add = Mock()
                mock_db.flush = Mock()
                mock_db.commit = Mock()
                mock_db.refresh = Mock()
                
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer valid-keycloak-token"}
                )
                
                # Verify user and tenant creation was attempted
                assert mock_db.add.call_count == 2  # One for tenant, one for user
                mock_db.commit.assert_called()

    @patch('app.services.keycloak_service.keycloak_service.validate_jwt_token')
    def test_existing_user_update_from_keycloak_token(self, mock_validate, client,
                                                     mock_keycloak_config, sample_keycloak_token_payload):
        """Test that existing users are updated from Keycloak token information."""
        mock_validate.return_value = sample_keycloak_token_payload
        
        with patch('app.core.security.select') as mock_select:
            with patch('app.db.session.get_db') as mock_get_db:
                mock_db = Mock(spec=AsyncSession)
                mock_get_db.return_value = mock_db
                
                # Mock existing user
                existing_user = User(
                    id=1,
                    username="keycloak:keycloak-user-123",
                    email="old.email@example.com",
                    tenant_id=1,
                    roles=["user"]
                )
                mock_user_result = Mock()
                mock_user_result.scalar_one_or_none.return_value = existing_user
                mock_db.execute.return_value = mock_user_result
                
                mock_db.commit = Mock()
                mock_db.refresh = Mock()
                
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": "Bearer valid-keycloak-token"}
                )
                
                # Verify user was updated
                assert existing_user.email == "john.doe@example.com"
                assert "admin" in existing_user.roles  # Should include mapped roles
                mock_db.commit.assert_called()

    def test_role_mapping_in_authentication(self, client, mock_keycloak_config):
        """Test that Keycloak roles are properly mapped during authentication."""
        token_payload = {
            "sub": "user-456",
            "preferred_username": "admin.user",
            "email": "admin@example.com",
            "realm_access": {
                "roles": ["realm-admin", "user"]
            },
            "resource_access": {
                "test-client": {
                    "roles": ["manager"]
                }
            },
            "tenant": "admin-org"
        }
        
        with patch('app.services.keycloak_service.keycloak_service.validate_jwt_token') as mock_validate:
            mock_validate.return_value = token_payload
            
            with patch('app.core.security.select') as mock_select:
                with patch('app.db.session.get_db') as mock_get_db:
                    mock_db = Mock(spec=AsyncSession)
                    mock_get_db.return_value = mock_db
                    
                    # Mock user doesn't exist
                    mock_user_result = Mock()
                    mock_user_result.scalar_one_or_none.return_value = None
                    
                    # Mock tenant exists
                    mock_tenant = Tenant(id=2, name="admin-org")
                    mock_tenant_result = Mock()
                    mock_tenant_result.scalar_one_or_none.return_value = mock_tenant
                    
                    mock_db.execute.side_effect = [mock_user_result, mock_tenant_result]
                    mock_db.add = Mock()
                    mock_db.commit = Mock()
                    mock_db.refresh = Mock()
                    
                    response = client.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": "Bearer admin-token"}
                    )
                    
                    # Verify the user was created with mapped roles
                    # realm-admin should map to admin, manager should map to manager
                    created_user_call = mock_db.add.call_args[0][0]
                    assert "admin" in created_user_call.roles
                    assert "manager" in created_user_call.roles

    def test_tenant_extraction_and_creation(self, client, mock_keycloak_config):
        """Test tenant extraction from token and automatic tenant creation."""
        token_payload = {
            "sub": "user-789",
            "preferred_username": "tenant.user",
            "email": "user@newcompany.com",
            "organization": "new-company",  # Using organization claim
            "realm_access": {"roles": ["user"]},
            "resource_access": {}
        }
        
        with patch('app.services.keycloak_service.keycloak_service.validate_jwt_token') as mock_validate:
            mock_validate.return_value = token_payload
            
            with patch('app.core.security.select') as mock_select:
                with patch('app.db.session.get_db') as mock_get_db:
                    mock_db = Mock(spec=AsyncSession)
                    mock_get_db.return_value = mock_db
                    
                    # Mock user doesn't exist
                    mock_user_result = Mock()
                    mock_user_result.scalar_one_or_none.return_value = None
                    
                    # Mock tenant doesn't exist
                    mock_tenant_result = Mock()
                    mock_tenant_result.scalar_one_or_none.return_value = None
                    
                    mock_db.execute.side_effect = [mock_user_result, mock_tenant_result]
                    mock_db.add = Mock()
                    mock_db.flush = Mock()
                    mock_db.commit = Mock()
                    mock_db.refresh = Mock()
                    
                    response = client.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": "Bearer tenant-token"}
                    )
                    
                    # Verify tenant was created with correct name
                    tenant_call = mock_db.add.call_args_list[0][0][0]
                    assert tenant_call.name == "new-company"

    @patch('app.services.keycloak_service.requests.get')
    def test_keycloak_service_error_handling(self, mock_get, client, mock_keycloak_config):
        """Test error handling when Keycloak service is unavailable."""
        # Mock network error when fetching JWKS
        mock_get.side_effect = Exception("Network error")
        
        with patch('app.services.keycloak_service.keycloak_service.validate_jwt_token') as mock_validate:
            # This should return None due to the network error
            mock_validate.return_value = None
            
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer some-token"}
            )
            
            assert response.status_code == 401