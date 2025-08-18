"""Tests for tenant context management and isolation."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

from app.auth.tenant_context import (
    TenantContext,
    tenant_context,
    TenantIsolationMixin,
    TenantAwareQueryBuilder,
    create_tenant_aware_query,
    get_current_tenant_context,
    require_tenant_context,
    validate_tenant_data_access,
    ensure_tenant_isolation
)
from app.auth.models import UserContext
from app.exceptions import AuthorizationError


class TestTenantContext:
    """Test TenantContext class."""
    
    @pytest.fixture
    def regular_user(self):
        """Regular user fixture."""
        return UserContext(
            user_id="regular-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    @pytest.fixture
    def admin_user(self):
        """Admin user fixture."""
        return UserContext(
            user_id="admin-user",
            tenant_id="tenant-a",
            roles=["admin"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    def test_tenant_context_creation(self, regular_user):
        """Test creating a tenant context."""
        context = TenantContext("tenant-a", regular_user)
        
        assert context.tenant_id == "tenant-a"
        assert context.user_context == regular_user
        assert not context.allow_cross_tenant
        assert not context.is_cross_tenant_access
        assert not context.is_admin_access
    
    def test_cross_tenant_detection(self, regular_user):
        """Test cross-tenant access detection."""
        # Same tenant
        same_tenant_context = TenantContext("tenant-a", regular_user)
        assert not same_tenant_context.is_cross_tenant_access
        
        # Different tenant
        cross_tenant_context = TenantContext("tenant-b", regular_user)
        assert cross_tenant_context.is_cross_tenant_access
    
    def test_admin_detection(self, admin_user):
        """Test admin access detection."""
        context = TenantContext("tenant-a", admin_user)
        assert context.is_admin_access
    
    def test_validate_access_same_tenant(self, regular_user):
        """Test access validation for same tenant."""
        context = TenantContext("tenant-a", regular_user)
        context.validate_access()  # Should not raise
    
    def test_validate_access_cross_tenant_denied(self, regular_user):
        """Test access validation denies cross-tenant access for regular users."""
        context = TenantContext("tenant-b", regular_user)
        
        with pytest.raises(AuthorizationError):
            context.validate_access()
    
    def test_validate_access_admin_cross_tenant(self, admin_user):
        """Test admin can access any tenant."""
        context = TenantContext("tenant-b", admin_user)
        context.validate_access()  # Should not raise
    
    def test_validate_access_cross_tenant_allowed(self, regular_user):
        """Test cross-tenant access when explicitly allowed."""
        context = TenantContext("tenant-b", regular_user, allow_cross_tenant=True)
        
        # Should still raise for regular user even when allowed
        with pytest.raises(AuthorizationError):
            context.validate_access()
    
    def test_add_tenant_filter(self, regular_user):
        """Test adding tenant filter to queries."""
        context = TenantContext("tenant-a", regular_user)
        
        query = {"search": "error", "limit": 100}
        filtered_query = context.add_tenant_filter(query)
        
        assert filtered_query["tenant_id"] == "tenant-a"
        assert filtered_query["search"] == "error"
        assert filtered_query["limit"] == 100
        
        # Original query should not be modified
        assert "tenant_id" not in query
    
    def test_add_tenant_filter_admin_cross_tenant(self, admin_user):
        """Test admin cross-tenant access doesn't add tenant filter."""
        context = TenantContext("tenant-b", admin_user, allow_cross_tenant=True)
        
        query = {"search": "error"}
        filtered_query = context.add_tenant_filter(query)
        
        # Should not add tenant filter for admin cross-tenant access
        assert "tenant_id" not in filtered_query
        assert filtered_query["search"] == "error"
    
    def test_filter_results_by_tenant(self, regular_user):
        """Test filtering results by tenant."""
        context = TenantContext("tenant-a", regular_user)
        
        results = [
            {"id": 1, "tenant_id": "tenant-a", "data": "test1"},
            {"id": 2, "tenant_id": "tenant-b", "data": "test2"},
            {"id": 3, "tenant_id": "tenant-a", "data": "test3"},
            {"id": 4, "data": "test4"},  # No tenant_id
        ]
        
        filtered_results = context.filter_results_by_tenant(results)
        
        assert len(filtered_results) == 2
        assert all(r["tenant_id"] == "tenant-a" for r in filtered_results)
        assert filtered_results[0]["id"] == 1
        assert filtered_results[1]["id"] == 3
    
    def test_filter_results_admin_cross_tenant(self, admin_user):
        """Test admin cross-tenant access doesn't filter results."""
        context = TenantContext("tenant-b", admin_user, allow_cross_tenant=True)
        
        results = [
            {"id": 1, "tenant_id": "tenant-a", "data": "test1"},
            {"id": 2, "tenant_id": "tenant-b", "data": "test2"},
        ]
        
        filtered_results = context.filter_results_by_tenant(results)
        
        # Should return all results for admin cross-tenant access
        assert len(filtered_results) == 2
        assert filtered_results == results
    
    def test_context_manager(self, regular_user):
        """Test TenantContext as context manager."""
        with TenantContext("tenant-a", regular_user) as context:
            assert context.tenant_id == "tenant-a"
            assert context.user_context == regular_user


class TestTenantContextFunction:
    """Test tenant_context function."""
    
    @pytest.fixture
    def regular_user(self):
        """Regular user fixture."""
        return UserContext(
            user_id="regular-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    def test_tenant_context_function(self, regular_user):
        """Test tenant_context context manager function."""
        with tenant_context("tenant-a", regular_user) as context:
            assert isinstance(context, TenantContext)
            assert context.tenant_id == "tenant-a"
            assert context.user_context == regular_user
            
            # Test that context is available globally
            current_context = get_current_tenant_context()
            assert current_context == context
        
        # Context should be cleared after exiting
        assert get_current_tenant_context() is None
    
    def test_tenant_context_validation_failure(self, regular_user):
        """Test tenant_context validates access on entry."""
        with pytest.raises(AuthorizationError):
            with tenant_context("tenant-b", regular_user):
                pass  # Should not reach here
    
    def test_require_tenant_context_success(self, regular_user):
        """Test require_tenant_context when context is active."""
        with tenant_context("tenant-a", regular_user) as context:
            required_context = require_tenant_context()
            assert required_context == context
    
    def test_require_tenant_context_failure(self):
        """Test require_tenant_context when no context is active."""
        with pytest.raises(RuntimeError, match="No tenant context is currently active"):
            require_tenant_context()


class TestTenantIsolationMixin:
    """Test TenantIsolationMixin."""
    
    @pytest.fixture
    def regular_user(self):
        """Regular user fixture."""
        return UserContext(
            user_id="regular-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    def test_mixin_methods(self, regular_user):
        """Test TenantIsolationMixin methods."""
        
        class TestService(TenantIsolationMixin):
            def process_data(self):
                query = {"search": "test"}
                filtered_query = self.add_tenant_filters(query)
                return filtered_query
        
        service = TestService()
        
        with tenant_context("tenant-a", regular_user):
            result = service.process_data()
            assert result["tenant_id"] == "tenant-a"
            assert result["search"] == "test"
    
    def test_mixin_filter_results(self, regular_user):
        """Test TenantIsolationMixin result filtering."""
        
        class TestService(TenantIsolationMixin):
            def get_data(self):
                results = [
                    {"id": 1, "tenant_id": "tenant-a", "data": "test1"},
                    {"id": 2, "tenant_id": "tenant-b", "data": "test2"},
                ]
                return self.filter_tenant_results(results)
        
        service = TestService()
        
        with tenant_context("tenant-a", regular_user):
            results = service.get_data()
            assert len(results) == 1
            assert results[0]["tenant_id"] == "tenant-a"
    
    def test_mixin_validate_tenant_access(self, regular_user):
        """Test TenantIsolationMixin tenant access validation."""
        
        class TestService(TenantIsolationMixin):
            def access_tenant_data(self, tenant_id):
                self.validate_tenant_access(tenant_id)
                return f"Accessing {tenant_id}"
        
        service = TestService()
        
        with tenant_context("tenant-a", regular_user):
            # Should work for same tenant
            result = service.access_tenant_data("tenant-a")
            assert result == "Accessing tenant-a"
            
            # Should fail for different tenant
            with pytest.raises(AuthorizationError):
                service.access_tenant_data("tenant-b")


class TestTenantAwareQueryBuilder:
    """Test TenantAwareQueryBuilder."""
    
    @pytest.fixture
    def regular_user(self):
        """Regular user fixture."""
        return UserContext(
            user_id="regular-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    def test_query_builder_basic(self):
        """Test basic query builder functionality."""
        builder = TenantAwareQueryBuilder()
        query = builder.add_filter("search", "error").add_filter("limit", 100).build()
        
        assert query["search"] == "error"
        assert query["limit"] == 100
    
    def test_query_builder_with_tenant_context(self, regular_user):
        """Test query builder with tenant context."""
        with tenant_context("tenant-a", regular_user):
            builder = TenantAwareQueryBuilder()
            query = builder.add_tenant_filter().add_filter("search", "error").build()
            
            assert query["tenant_id"] == "tenant-a"
            assert query["search"] == "error"
    
    def test_query_builder_explicit_tenant(self, regular_user):
        """Test query builder with explicit tenant."""
        with tenant_context("tenant-a", regular_user):
            builder = TenantAwareQueryBuilder()
            query = builder.add_tenant_filter("tenant-a").build()
            
            assert query["tenant_id"] == "tenant-a"
    
    def test_query_builder_cross_tenant_denied(self, regular_user):
        """Test query builder denies cross-tenant access."""
        with tenant_context("tenant-a", regular_user):
            builder = TenantAwareQueryBuilder()
            
            with pytest.raises(AuthorizationError):
                builder.add_tenant_filter("tenant-b")
    
    def test_query_builder_time_range(self):
        """Test query builder time range functionality."""
        builder = TenantAwareQueryBuilder()
        query = builder.add_time_range("2023-01-01", "2023-01-31").build()
        
        assert query["start_time"] == "2023-01-01"
        assert query["end_time"] == "2023-01-31"
    
    def test_create_tenant_aware_query(self, regular_user):
        """Test create_tenant_aware_query helper function."""
        with tenant_context("tenant-a", regular_user):
            query = create_tenant_aware_query({"search": "test"}).add_tenant_filter().build()
            
            assert query["tenant_id"] == "tenant-a"
            assert query["search"] == "test"


class TestTenantDataValidation:
    """Test tenant data validation functions."""
    
    @pytest.fixture
    def regular_user(self):
        """Regular user fixture."""
        return UserContext(
            user_id="regular-user",
            tenant_id="tenant-a",
            roles=["user"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    
    def test_validate_tenant_data_access_success(self, regular_user):
        """Test successful tenant data validation."""
        data = {"id": 1, "tenant_id": "tenant-a", "content": "test"}
        
        with tenant_context("tenant-a", regular_user):
            validate_tenant_data_access(data)  # Should not raise
    
    def test_validate_tenant_data_access_failure(self, regular_user):
        """Test tenant data validation failure."""
        data = {"id": 1, "tenant_id": "tenant-b", "content": "test"}
        
        with tenant_context("tenant-a", regular_user):
            with pytest.raises(AuthorizationError):
                validate_tenant_data_access(data)
    
    def test_validate_tenant_data_no_context(self):
        """Test tenant data validation without context."""
        data = {"id": 1, "tenant_id": "tenant-b", "content": "test"}
        
        # Should not raise when no context is active
        validate_tenant_data_access(data)
    
    def test_validate_tenant_data_no_tenant_id(self, regular_user):
        """Test tenant data validation with data that has no tenant_id."""
        data = {"id": 1, "content": "test"}  # No tenant_id
        
        with tenant_context("tenant-a", regular_user):
            validate_tenant_data_access(data)  # Should not raise
    
    def test_ensure_tenant_isolation_decorator(self, regular_user):
        """Test ensure_tenant_isolation decorator."""
        
        @ensure_tenant_isolation
        def process_data(data):
            return f"Processing {data}"
        
        with tenant_context("tenant-a", regular_user):
            result = process_data("test")
            assert result == "Processing test"