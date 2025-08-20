"""Tests for Role-Based Access Control (RBAC) functionality."""

import pytest
from datetime import datetime, timezone, timedelta

from app.auth.rbac import RBACManager, Permission, Role, require_permission, require_any_permission
from app.auth.models import UserContext
from app.exceptions import AuthorizationError


class TestRBACManager:
    """Test RBAC manager functionality."""
    
    @pytest.fixture
    def rbac_manager(self):
        """RBAC manager fixture."""
        return RBACManager()
    
    @pytest.fixture
    def admin_user(self):
        """Admin user fixture."""
        return UserContext(
            user_id="admin-user",
            tenant_id="test-tenant",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    @pytest.fixture
    def viewer_user(self):
        """Viewer user fixture."""
        return UserContext(
            user_id="viewer-user",
            tenant_id="test-tenant",
            roles=["viewer"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    @pytest.fixture
    def editor_user(self):
        """Editor user fixture."""
        return UserContext(
            user_id="editor-user",
            tenant_id="test-tenant",
            roles=["editor"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    @pytest.fixture
    def analyst_user(self):
        """Analyst user fixture."""
        return UserContext(
            user_id="analyst-user",
            tenant_id="test-tenant",
            roles=["analyst"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    def test_admin_permissions(self, rbac_manager, admin_user):
        """Test admin user has all permissions."""
        # Test various permissions
        assert rbac_manager.has_permission(admin_user, Permission.LOGS_READ)
        assert rbac_manager.has_permission(admin_user, Permission.LOGS_WRITE)
        assert rbac_manager.has_permission(admin_user, Permission.ALERTS_WRITE)
        assert rbac_manager.has_permission(admin_user, Permission.TENANT_MANAGE)
        assert rbac_manager.has_permission(admin_user, Permission.SYSTEM_CONFIG)
        
        # Admin should have all permissions
        all_permissions = rbac_manager.get_user_permissions(admin_user)
        assert len(all_permissions) == len(Permission)
    
    def test_viewer_permissions(self, rbac_manager, viewer_user):
        """Test viewer user permissions."""
        # Viewer should have read permissions
        assert rbac_manager.has_permission(viewer_user, Permission.LOGS_READ)
        assert rbac_manager.has_permission(viewer_user, Permission.METRICS_READ)
        assert rbac_manager.has_permission(viewer_user, Permission.TRACES_READ)
        assert rbac_manager.has_permission(viewer_user, Permission.ALERTS_READ)
        assert rbac_manager.has_permission(viewer_user, Permission.SEARCH_READ)
        assert rbac_manager.has_permission(viewer_user, Permission.INSIGHTS_READ)
        assert rbac_manager.has_permission(viewer_user, Permission.PROFILE_READ)
        
        # Viewer should not have write permissions
        assert not rbac_manager.has_permission(viewer_user, Permission.LOGS_WRITE)
        assert not rbac_manager.has_permission(viewer_user, Permission.ALERTS_WRITE)
        assert not rbac_manager.has_permission(viewer_user, Permission.PROFILE_WRITE)
        assert not rbac_manager.has_permission(viewer_user, Permission.TENANT_MANAGE)
    
    def test_editor_permissions(self, rbac_manager, editor_user):
        """Test editor user permissions."""
        # Editor should have read permissions
        assert rbac_manager.has_permission(editor_user, Permission.LOGS_READ)
        assert rbac_manager.has_permission(editor_user, Permission.ALERTS_READ)
        
        # Editor should have alert management permissions
        assert rbac_manager.has_permission(editor_user, Permission.ALERTS_WRITE)
        assert rbac_manager.has_permission(editor_user, Permission.ALERTS_ACKNOWLEDGE)
        assert rbac_manager.has_permission(editor_user, Permission.ALERTS_RESOLVE)
        assert rbac_manager.has_permission(editor_user, Permission.ALERTS_ASSIGN)
        
        # Editor should have profile write permission
        assert rbac_manager.has_permission(editor_user, Permission.PROFILE_WRITE)
        
        # Editor should not have admin permissions
        assert not rbac_manager.has_permission(editor_user, Permission.TENANT_MANAGE)
        assert not rbac_manager.has_permission(editor_user, Permission.SYSTEM_CONFIG)
        assert not rbac_manager.has_permission(editor_user, Permission.LOGS_WRITE)
    
    def test_analyst_permissions(self, rbac_manager, analyst_user):
        """Test analyst user permissions."""
        # Analyst should have read permissions
        assert rbac_manager.has_permission(analyst_user, Permission.LOGS_READ)
        assert rbac_manager.has_permission(analyst_user, Permission.METRICS_READ)
        assert rbac_manager.has_permission(analyst_user, Permission.TRACES_READ)
        
        # Analyst should have advanced search and insights permissions
        assert rbac_manager.has_permission(analyst_user, Permission.SEARCH_ADVANCED)
        assert rbac_manager.has_permission(analyst_user, Permission.SEARCH_EXPORT)
        assert rbac_manager.has_permission(analyst_user, Permission.INSIGHTS_WRITE)
        assert rbac_manager.has_permission(analyst_user, Permission.INSIGHTS_EXPORT)
        
        # Analyst should not have admin or alert write permissions
        assert not rbac_manager.has_permission(analyst_user, Permission.ALERTS_WRITE)
        assert not rbac_manager.has_permission(analyst_user, Permission.TENANT_MANAGE)
    
    def test_multiple_roles(self, rbac_manager):
        """Test user with multiple roles gets combined permissions."""
        multi_role_user = UserContext(
            user_id="multi-user",
            tenant_id="test-tenant",
            roles=["viewer", "editor"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        # Should have permissions from both roles
        assert rbac_manager.has_permission(multi_role_user, Permission.LOGS_READ)  # From viewer
        assert rbac_manager.has_permission(multi_role_user, Permission.ALERTS_WRITE)  # From editor
        assert rbac_manager.has_permission(multi_role_user, Permission.PROFILE_WRITE)  # From editor
    
    def test_has_any_permission(self, rbac_manager, viewer_user, editor_user):
        """Test has_any_permission method."""
        read_permissions = [Permission.LOGS_READ, Permission.METRICS_READ]
        write_permissions = [Permission.LOGS_WRITE, Permission.ALERTS_WRITE]
        
        # Viewer should have read permissions
        assert rbac_manager.has_any_permission(viewer_user, read_permissions)
        
        # Viewer should not have write permissions
        assert not rbac_manager.has_any_permission(viewer_user, write_permissions)
        
        # Editor should have write permissions
        assert rbac_manager.has_any_permission(editor_user, write_permissions)
    
    def test_has_all_permissions(self, rbac_manager, admin_user, viewer_user):
        """Test has_all_permissions method."""
        read_permissions = [Permission.LOGS_READ, Permission.METRICS_READ, Permission.ALERTS_READ]
        mixed_permissions = [Permission.LOGS_READ, Permission.LOGS_WRITE]
        
        # Admin should have all permissions
        assert rbac_manager.has_all_permissions(admin_user, read_permissions)
        assert rbac_manager.has_all_permissions(admin_user, mixed_permissions)
        
        # Viewer should have all read permissions but not write
        assert rbac_manager.has_all_permissions(viewer_user, read_permissions)
        assert not rbac_manager.has_all_permissions(viewer_user, mixed_permissions)
    
    def test_tenant_access_validation(self, rbac_manager):
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
        
        # User can access their own tenant
        assert rbac_manager.can_access_tenant(user, "tenant-a")
        rbac_manager.validate_tenant_access(user, "tenant-a")  # Should not raise
        
        # User cannot access other tenant
        assert not rbac_manager.can_access_tenant(user, "tenant-b")
        with pytest.raises(AuthorizationError):
            rbac_manager.validate_tenant_access(user, "tenant-b")
        
        # Admin can access any tenant
        assert rbac_manager.can_access_tenant(admin_user, "tenant-b")
        rbac_manager.validate_tenant_access(admin_user, "tenant-b")  # Should not raise
    
    def test_permission_validation(self, rbac_manager, viewer_user):
        """Test permission validation with exceptions."""
        # Valid permission should not raise
        rbac_manager.validate_permission(viewer_user, Permission.LOGS_READ)
        
        # Invalid permission should raise
        with pytest.raises(AuthorizationError):
            rbac_manager.validate_permission(viewer_user, Permission.TENANT_MANAGE)
    
    def test_dynamic_role_permissions(self, rbac_manager, viewer_user):
        """Test adding and removing permissions from roles."""
        # Initially viewer doesn't have write permission
        assert not rbac_manager.has_permission(viewer_user, Permission.LOGS_WRITE)
        
        # Add write permission to viewer role
        rbac_manager.add_role_permission("viewer", Permission.LOGS_WRITE)
        
        # Now viewer should have write permission
        assert rbac_manager.has_permission(viewer_user, Permission.LOGS_WRITE)
        
        # Remove the permission
        rbac_manager.remove_role_permission("viewer", Permission.LOGS_WRITE)
        
        # Should no longer have write permission
        assert not rbac_manager.has_permission(viewer_user, Permission.LOGS_WRITE)


class TestRBACDecorators:
    """Test RBAC decorators."""
    
    @pytest.fixture
    def admin_user(self):
        """Admin user fixture."""
        return UserContext(
            user_id="admin-user",
            tenant_id="test-tenant",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    @pytest.fixture
    def viewer_user(self):
        """Viewer user fixture."""
        return UserContext(
            user_id="viewer-user",
            tenant_id="test-tenant",
            roles=["viewer"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    def test_require_permission_decorator_success(self, admin_user):
        """Test require_permission decorator with valid permission."""
        
        @require_permission(Permission.LOGS_READ)
        def read_logs(user_context: UserContext):
            return f"Reading logs for {user_context.user_id}"
        
        # Should work for admin user
        result = read_logs(admin_user)
        assert result == "Reading logs for admin-user"
    
    def test_require_permission_decorator_failure(self, viewer_user):
        """Test require_permission decorator with invalid permission."""
        
        @require_permission(Permission.TENANT_MANAGE)
        def manage_tenant(user_context: UserContext):
            return "Managing tenant"
        
        # Should raise exception for viewer user
        with pytest.raises(AuthorizationError):
            manage_tenant(viewer_user)
    
    def test_require_any_permission_decorator_success(self, viewer_user):
        """Test require_any_permission decorator with valid permissions."""
        
        @require_any_permission([Permission.LOGS_READ, Permission.METRICS_READ])
        def read_data(user_context: UserContext):
            return f"Reading data for {user_context.user_id}"
        
        # Should work for viewer user (has read permissions)
        result = read_data(viewer_user)
        assert result == "Reading data for viewer-user"
    
    def test_require_any_permission_decorator_failure(self, viewer_user):
        """Test require_any_permission decorator with invalid permissions."""
        
        @require_any_permission([Permission.TENANT_MANAGE, Permission.SYSTEM_CONFIG])
        def admin_function(user_context: UserContext):
            return "Admin function"
        
        # Should raise exception for viewer user
        with pytest.raises(AuthorizationError):
            admin_function(viewer_user)
    
    def test_decorator_with_kwargs(self, admin_user):
        """Test decorator works with keyword arguments."""
        
        @require_permission(Permission.LOGS_READ)
        def read_logs_with_kwargs(query: str, user_context: UserContext):
            return f"Query: {query}, User: {user_context.user_id}"
        
        result = read_logs_with_kwargs(query="error", user_context=admin_user)
        assert result == "Query: error, User: admin-user"
    
    def test_decorator_missing_user_context(self):
        """Test decorator raises error when user context is missing."""
        
        @require_permission(Permission.LOGS_READ)
        def read_logs_no_context(query: str):
            return f"Query: {query}"
        
        with pytest.raises(AuthorizationError, match="User context not found"):
            read_logs_no_context("test")


class TestPermissionEnum:
    """Test Permission enum values."""
    
    def test_permission_values(self):
        """Test that permission enum has expected values."""
        # Test some key permissions exist
        assert Permission.LOGS_READ.value == "logs:read"
        assert Permission.LOGS_WRITE.value == "logs:write"
        assert Permission.ALERTS_READ.value == "alerts:read"
        assert Permission.ALERTS_WRITE.value == "alerts:write"
        assert Permission.TENANT_MANAGE.value == "tenant:manage"
        assert Permission.SYSTEM_CONFIG.value == "system:config"
    
    def test_role_values(self):
        """Test that role enum has expected values."""
        assert Role.ADMIN.value == "admin"
        assert Role.USER.value == "user"
        assert Role.VIEWER.value == "viewer"
        assert Role.EDITOR.value == "editor"
        assert Role.ANALYST.value == "analyst"
        assert Role.TENANT_ADMIN.value == "tenant_admin"