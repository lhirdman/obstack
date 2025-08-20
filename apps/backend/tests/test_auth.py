"""Tests for authentication functionality."""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import Mock, patch

from app.main import app
from app.auth.jwt_handler import JWTHandler
from app.auth.service import AuthService
from app.auth.models import UserContext
from app.auth.rbac import RBACManager, Permission, Role, rbac_manager
from app.auth.tenant_context import TenantContext, tenant_context, TenantIsolationMixin
from app.models.auth import LoginRequest, RefreshTokenRequest
from app.exceptions import AuthenticationError, AuthorizationError


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def jwt_handler():
    """JWT handler fixture."""
    return JWTHandler(secret_key="test-secret-key")


@pytest.fixture
def auth_service():
    """Auth service fixture."""
    return AuthService(jwt_handler=JWTHandler(secret_key="test-secret-key"))


class TestJWTHandler:
    """Test JWT token handling."""
    
    def test_create_access_token(self, jwt_handler):
        """Test access token creation."""
        token = jwt_handler.create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user", "viewer"]
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self, jwt_handler):
        """Test refresh token creation."""
        token = jwt_handler.create_refresh_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user", "viewer"]
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_validate_token_success(self, jwt_handler):
        """Test successful token validation."""
        token = jwt_handler.create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user", "viewer"]
        )
        
        user_context = jwt_handler.validate_token(token)
        
        assert user_context.user_id == "test-user"
        assert user_context.tenant_id == "test-tenant"
        assert user_context.roles == ["user", "viewer"]
        assert user_context.has_role("user")
        assert user_context.has_role("viewer")
        assert not user_context.has_role("admin")
    
    def test_validate_expired_token(self, jwt_handler):
        """Test validation of expired token."""
        # Create token with very short expiration
        token = jwt_handler.create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user"],
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="Token has expired"):
            jwt_handler.validate_token(token)
    
    def test_validate_invalid_token(self, jwt_handler):
        """Test validation of invalid token."""
        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="Invalid token"):
            jwt_handler.validate_token("invalid-token")
    
    def test_validate_refresh_token(self, jwt_handler):
        """Test refresh token validation."""
        token = jwt_handler.create_refresh_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user", "viewer"]
        )
        
        refresh_context = jwt_handler.validate_refresh_token(token)
        
        assert refresh_context.user_id == "test-user"
        assert refresh_context.tenant_id == "test-tenant"
        assert refresh_context.roles == ["user", "viewer"]


class TestAuthService:
    """Test authentication service."""
    
    @pytest.mark.asyncio
    async def test_authenticate_demo_user(self, auth_service):
        """Test demo user authentication."""
        login_request = LoginRequest(
            username="demo",
            password="demo",
            tenant_id="test-tenant"
        )
        
        tokens = await auth_service.authenticate_user(login_request)
        
        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.token_type == "Bearer"
        assert tokens.expires_in > 0
    
    @pytest.mark.asyncio
    async def test_authenticate_admin_user(self, auth_service):
        """Test admin user authentication."""
        login_request = LoginRequest(
            username="admin",
            password="admin",
            tenant_id="test-tenant"
        )
        
        tokens = await auth_service.authenticate_user(login_request)
        
        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.token_type == "Bearer"
        assert tokens.expires_in > 0
    
    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self, auth_service):
        """Test authentication with invalid credentials."""
        login_request = LoginRequest(
            username="invalid",
            password="invalid"
        )
        
        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            await auth_service.authenticate_user(login_request)
    
    @pytest.mark.asyncio
    async def test_refresh_tokens(self, auth_service):
        """Test token refresh."""
        # First authenticate to get tokens
        login_request = LoginRequest(
            username="demo",
            password="demo"
        )
        
        initial_tokens = await auth_service.authenticate_user(login_request)
        
        # Now refresh the tokens
        refresh_request = RefreshTokenRequest(
            refresh_token=initial_tokens.refresh_token
        )
        
        new_tokens = await auth_service.refresh_tokens(refresh_request)
        
        assert new_tokens.access_token
        assert new_tokens.refresh_token
        assert new_tokens.access_token != initial_tokens.access_token
        assert new_tokens.refresh_token != initial_tokens.refresh_token


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post("/api/auth/login", json={
            "username": "demo",
            "password": "demo"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post("/api/auth/login", json={
            "username": "invalid",
            "password": "invalid"
        })
        
        assert response.status_code == 401
    
    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = client.post("/api/auth/login", json={
            "username": "demo",
            "password": "demo"
        })
        
        tokens = login_response.json()
        
        # Now refresh
        refresh_response = client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]
        })
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.post("/api/search", json={
            "query": "test",
            "type": "logs"
        })
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_token(self, client):
        """Test accessing protected endpoint with valid token."""
        # First login to get token
        login_response = client.post("/api/auth/login", json={
            "username": "demo",
            "password": "demo"
        })
        
        tokens = login_response.json()
        
        # Use token to access protected endpoint
        response = client.post(
            "/api/search",
            json={
                "query": "test",
                "type": "logs"
            },
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        
        assert response.status_code == 200
    
    def test_get_current_user_profile(self, client):
        """Test getting current user profile."""
        # First login to get token
        login_response = client.post("/api/auth/login", json={
            "username": "demo",
            "password": "demo"
        })
        
        tokens = login_response.json()
        
        # Get user profile
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        
        assert response.status_code == 200
        profile = response.json()
        assert "id" in profile
        assert "username" in profile
        assert "tenant_id" in profile
        assert "roles" in profile


class TestUserContext:
    """Test UserContext model."""
    
    def test_has_role(self):
        """Test role checking."""
        user_context = UserContext(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user", "viewer"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        assert user_context.has_role("user")
        assert user_context.has_role("viewer")
        assert not user_context.has_role("admin")
    
    def test_has_any_role(self):
        """Test checking for any of multiple roles."""
        user_context = UserContext(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user", "viewer"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        assert user_context.has_any_role(["admin", "user"])
        assert user_context.has_any_role(["viewer", "editor"])
        assert not user_context.has_any_role(["admin", "editor"])
    
    def test_is_admin(self):
        """Test admin role checking."""
        admin_user = UserContext(
            user_id="admin-user",
            tenant_id="test-tenant",
            roles=["admin", "user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        regular_user = UserContext(
            user_id="regular-user",
            tenant_id="test-tenant",
            roles=["user", "viewer"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        assert admin_user.is_admin()
        assert not regular_user.is_admin()


class TestRBACManager:
    """Test role-based access control manager."""
    
    def test_admin_has_all_permissions(self):
        """Test that admin role has all permissions."""
        admin_user = UserContext(
            user_id="admin-user",
            tenant_id="test-tenant",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        rbac = RBACManager()
        
        # Test various permissions
        assert rbac.has_permission(admin_user, Permission.LOGS_READ)
        assert rbac.has_permission(admin_user, Permission.ALERTS_WRITE)
        assert rbac.has_permission(admin_user, Permission.TENANT_MANAGE)
        assert rbac.has_permission(admin_user, Permission.SYSTEM_CONFIG)
    
    def test_viewer_permissions(self):
        """Test viewer role permissions."""
        viewer_user = UserContext(
            user_id="viewer-user",
            tenant_id="test-tenant",
            roles=["viewer"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        rbac = RBACManager()
        
        # Viewer should have read permissions
        assert rbac.has_permission(viewer_user, Permission.LOGS_READ)
        assert rbac.has_permission(viewer_user, Permission.METRICS_READ)
        assert rbac.has_permission(viewer_user, Permission.ALERTS_READ)
        
        # Viewer should not have write permissions
        assert not rbac.has_permission(viewer_user, Permission.LOGS_WRITE)
        assert not rbac.has_permission(viewer_user, Permission.ALERTS_WRITE)
        assert not rbac.has_permission(viewer_user, Permission.TENANT_MANAGE)
    
    def test_editor_permissions(self):
        """Test editor role permissions."""
        editor_user = UserContext(
            user_id="editor-user",
            tenant_id="test-tenant",
            roles=["editor"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        rbac = RBACManager()
        
        # Editor should have read permissions
        assert rbac.has_permission(editor_user, Permission.LOGS_READ)
        assert rbac.has_permission(editor_user, Permission.ALERTS_READ)
        
        # Editor should have alert management permissions
        assert rbac.has_permission(editor_user, Permission.ALERTS_WRITE)
        assert rbac.has_permission(editor_user, Permission.ALERTS_ACKNOWLEDGE)
        
        # Editor should not have admin permissions
        assert not rbac.has_permission(editor_user, Permission.TENANT_MANAGE)
        assert not rbac.has_permission(editor_user, Permission.SYSTEM_CONFIG)
    
    def test_multiple_roles(self):
        """Test user with multiple roles."""
        multi_role_user = UserContext(
            user_id="multi-user",
            tenant_id="test-tenant",
            roles=["viewer", "editor"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        rbac = RBACManager()
        
        # Should have permissions from both roles
        assert rbac.has_permission(multi_role_user, Permission.LOGS_READ)  # From viewer
        assert rbac.has_permission(multi_role_user, Permission.ALERTS_WRITE)  # From editor
    
    def test_tenant_access_validation(self):
        """Test tenant access validation."""
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        admin_user = UserContext(
            user_id="admin-user",
            tenant_id="tenant-a",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        rbac = RBACManager()
        
        # User can access their own tenant
        assert rbac.can_access_tenant(user, "tenant-a")
        
        # User cannot access other tenant
        assert not rbac.can_access_tenant(user, "tenant-b")
        
        # Admin can access any tenant
        assert rbac.can_access_tenant(admin_user, "tenant-a")
        assert rbac.can_access_tenant(admin_user, "tenant-b")
    
    def test_permission_validation_raises_error(self):
        """Test that permission validation raises error for unauthorized access."""
        user = UserContext(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["viewer"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        rbac = RBACManager()
        
        # Should raise error for unauthorized permission
        with pytest.raises(AuthorizationError):
            rbac.validate_permission(user, Permission.TENANT_MANAGE)
    
    def test_tenant_validation_raises_error(self):
        """Test that tenant validation raises error for unauthorized access."""
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        rbac = RBACManager()
        
        # Should raise error for unauthorized tenant access
        with pytest.raises(AuthorizationError):
            rbac.validate_tenant_access(user, "tenant-b")


class TestTenantContext:
    """Test tenant context management."""
    
    def test_tenant_context_creation(self):
        """Test creating tenant context."""
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        context = TenantContext("tenant-a", user)
        
        assert context.tenant_id == "tenant-a"
        assert context.user_context == user
        assert not context.is_cross_tenant_access
    
    def test_cross_tenant_access_detection(self):
        """Test cross-tenant access detection."""
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # Same tenant access
        same_tenant_context = TenantContext("tenant-a", user)
        assert not same_tenant_context.is_cross_tenant_access
        
        # Cross-tenant access
        cross_tenant_context = TenantContext("tenant-b", user)
        assert cross_tenant_context.is_cross_tenant_access
    
    def test_tenant_context_validation(self):
        """Test tenant context access validation."""
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # Valid access to own tenant
        valid_context = TenantContext("tenant-a", user)
        valid_context.validate_access()  # Should not raise
        
        # Invalid cross-tenant access
        invalid_context = TenantContext("tenant-b", user)
        with pytest.raises(AuthorizationError):
            invalid_context.validate_access()
    
    def test_admin_cross_tenant_access(self):
        """Test that admin can access any tenant."""
        admin_user = UserContext(
            user_id="admin-user",
            tenant_id="tenant-a",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # Admin can access other tenants
        cross_tenant_context = TenantContext("tenant-b", admin_user)
        cross_tenant_context.validate_access()  # Should not raise
    
    def test_tenant_filter_addition(self):
        """Test adding tenant filters to queries."""
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        context = TenantContext("tenant-a", user)
        
        query = {"search": "error"}
        filtered_query = context.add_tenant_filter(query)
        
        assert filtered_query["tenant_id"] == "tenant-a"
        assert filtered_query["search"] == "error"
    
    def test_admin_cross_tenant_no_filter(self):
        """Test that admin cross-tenant access doesn't add tenant filter."""
        admin_user = UserContext(
            user_id="admin-user",
            tenant_id="tenant-a",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        context = TenantContext("tenant-b", admin_user, allow_cross_tenant=True)
        
        query = {"search": "error"}
        filtered_query = context.add_tenant_filter(query)
        
        # Should not add tenant filter for admin cross-tenant access
        assert "tenant_id" not in filtered_query
        assert filtered_query["search"] == "error"
    
    def test_results_filtering(self):
        """Test filtering results by tenant."""
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        context = TenantContext("tenant-a", user)
        
        results = [
            {"id": 1, "tenant_id": "tenant-a", "data": "test1"},
            {"id": 2, "tenant_id": "tenant-b", "data": "test2"},
            {"id": 3, "tenant_id": "tenant-a", "data": "test3"},
        ]
        
        filtered_results = context.filter_results_by_tenant(results)
        
        assert len(filtered_results) == 2
        assert all(r["tenant_id"] == "tenant-a" for r in filtered_results)
    
    def test_context_manager(self):
        """Test tenant context as context manager."""
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        with tenant_context("tenant-a", user) as context:
            assert context.tenant_id == "tenant-a"
            assert context.user_context == user


class TestTenantIsolationMixin:
    """Test tenant isolation mixin."""
    
    def test_mixin_functionality(self):
        """Test tenant isolation mixin methods."""
        
        class TestService(TenantIsolationMixin):
            pass
        
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        service = TestService()
        
        with tenant_context("tenant-a", user):
            # Test adding tenant filters
            query = {"search": "test"}
            filtered_query = service.add_tenant_filters(query)
            assert filtered_query["tenant_id"] == "tenant-a"
            
            # Test tenant access validation
            service.validate_tenant_access("tenant-a")  # Should not raise
            
            with pytest.raises(AuthorizationError):
                service.validate_tenant_access("tenant-b")


class TestDependencies:
    """Test FastAPI dependencies for authentication and authorization."""
    
    def test_require_roles_dependency(self):
        """Test role requirement dependency."""
        from app.auth.dependencies import require_roles
        
        # Create dependency function
        admin_required = require_roles(["admin"])
        
        # Test with admin user
        admin_user = UserContext(
            user_id="admin-user",
            tenant_id="test-tenant",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # Should return user context for admin
        result = admin_required(admin_user)
        assert result == admin_user
        
        # Test with non-admin user
        regular_user = UserContext(
            user_id="regular-user",
            tenant_id="test-tenant",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # Should raise HTTPException for non-admin
        with pytest.raises(HTTPException) as exc_info:
            admin_required(regular_user)
        
        assert exc_info.value.status_code == 403
    
    def test_tenant_access_dependency(self):
        """Test tenant access requirement dependency."""
        from app.auth.dependencies import require_tenant_access
        
        user = UserContext(
            user_id="test-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # Create dependency for tenant-a
        tenant_a_required = require_tenant_access("tenant-a")
        
        # Should allow access to own tenant
        result = tenant_a_required(user)
        assert result == user
        
        # Create dependency for tenant-b
        tenant_b_required = require_tenant_access("tenant-b")
        
        # Should deny access to other tenant
        with pytest.raises(HTTPException) as exc_info:
            tenant_b_required(user)
        
        assert exc_info.value.status_code == 403
    
    def test_admin_cross_tenant_access(self):
        """Test admin cross-tenant access in dependencies."""
        from app.auth.dependencies import require_tenant_access
        
        admin_user = UserContext(
            user_id="admin-user",
            tenant_id="tenant-a",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # Admin should be able to access any tenant
        tenant_b_required = require_tenant_access("tenant-b")
        result = tenant_b_required(admin_user)
        assert result == admin_user