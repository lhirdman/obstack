"""Unit tests for tenant service."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.tenant_service import TenantService
from app.models.tenant import (
    TenantCreate, TenantUpdate, TenantStatus, TenantSettings, DataRetentionPolicy
)
from app.exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError, TenantOperationError
)


@pytest.mark.asyncio
class TestTenantService:
    """Test cases for TenantService."""
    
    @pytest.fixture
    def tenant_service(self):
        """Create tenant service instance for testing."""
        return TenantService()
    
    @pytest.fixture
    def sample_tenant_create(self):
        """Sample tenant creation data."""
        return TenantCreate(
            name="Test Tenant",
            domain="test-tenant",
            description="A test tenant",
            admin_email="admin@test.com",
            admin_username="admin",
            settings=TenantSettings(
                max_users=50,
                max_dashboards=100,
                features_enabled=["search", "alerts"]
            ),
            retention_policy=DataRetentionPolicy(
                logs_retention_days=30,
                metrics_retention_days=90
            )
        )
    
    @pytest.fixture
    def sample_tenant_update(self):
        """Sample tenant update data."""
        return TenantUpdate(
            name="Updated Tenant",
            description="Updated description",
            status=TenantStatus.SUSPENDED
        )
    
    async def test_create_tenant_success(self, tenant_service, sample_tenant_create):
        """Test successful tenant creation."""
        # Mock the domain existence check
        tenant_service._domain_exists = AsyncMock(return_value=False)
        tenant_service._store_tenant = AsyncMock()
        tenant_service._create_tenant_admin = AsyncMock()
        tenant_service._log_audit_event = AsyncMock()
        tenant_service._initialize_tenant_resources = AsyncMock()
        
        # Create tenant
        tenant = await tenant_service.create_tenant(sample_tenant_create, "admin-user-id")
        
        # Assertions
        assert tenant.name == sample_tenant_create.name
        assert tenant.domain == sample_tenant_create.domain
        assert tenant.description == sample_tenant_create.description
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.id is not None
        assert tenant.created_at is not None
        assert tenant.updated_at is not None
        
        # Verify mocks were called
        tenant_service._domain_exists.assert_called_once_with(sample_tenant_create.domain)
        tenant_service._store_tenant.assert_called_once()
        tenant_service._create_tenant_admin.assert_called_once()
        tenant_service._log_audit_event.assert_called_once()
        tenant_service._initialize_tenant_resources.assert_called_once()
    
    async def test_create_tenant_domain_exists(self, tenant_service, sample_tenant_create):
        """Test tenant creation with existing domain."""
        # Mock domain exists
        tenant_service._domain_exists = AsyncMock(return_value=True)
        
        # Attempt to create tenant
        with pytest.raises(TenantAlreadyExistsError) as exc_info:
            await tenant_service.create_tenant(sample_tenant_create, "admin-user-id")
        
        assert "already exists" in str(exc_info.value)
    
    async def test_create_tenant_operation_error(self, tenant_service, sample_tenant_create):
        """Test tenant creation with operation error."""
        # Mock domain check to pass but store to fail
        tenant_service._domain_exists = AsyncMock(return_value=False)
        tenant_service._store_tenant = AsyncMock(side_effect=Exception("Database error"))
        
        # Attempt to create tenant
        with pytest.raises(TenantOperationError) as exc_info:
            await tenant_service.create_tenant(sample_tenant_create, "admin-user-id")
        
        assert "Failed to create tenant" in str(exc_info.value)
    
    async def test_get_tenant_from_cache(self, tenant_service):
        """Test getting tenant from cache."""
        # Setup cache
        tenant_id = "test-tenant-id"
        cached_tenant = MagicMock()
        cached_tenant.id = tenant_id
        tenant_service._tenant_cache[tenant_id] = cached_tenant
        tenant_service._last_cache_update[tenant_id] = datetime.utcnow()
        
        # Get tenant
        result = await tenant_service.get_tenant(tenant_id)
        
        # Assertions
        assert result == cached_tenant
    
    async def test_get_tenant_from_database(self, tenant_service):
        """Test getting tenant from database when not cached."""
        tenant_id = "test-tenant-id"
        db_tenant = MagicMock()
        db_tenant.id = tenant_id
        
        # Mock database fetch
        tenant_service._fetch_tenant_by_id = AsyncMock(return_value=db_tenant)
        
        # Get tenant
        result = await tenant_service.get_tenant(tenant_id)
        
        # Assertions
        assert result == db_tenant
        assert tenant_id in tenant_service._tenant_cache
        tenant_service._fetch_tenant_by_id.assert_called_once_with(tenant_id)
    
    async def test_get_tenant_not_found(self, tenant_service):
        """Test getting non-existent tenant."""
        tenant_id = "non-existent-tenant"
        
        # Mock database fetch to return None
        tenant_service._fetch_tenant_by_id = AsyncMock(return_value=None)
        
        # Get tenant
        result = await tenant_service.get_tenant(tenant_id)
        
        # Assertions
        assert result is None
    
    async def test_get_tenant_by_domain_success(self, tenant_service):
        """Test getting tenant by domain."""
        domain = "test-domain"
        tenant = MagicMock()
        tenant.domain = domain
        
        # Mock database fetch
        tenant_service._fetch_tenant_by_domain = AsyncMock(return_value=tenant)
        
        # Get tenant by domain
        result = await tenant_service.get_tenant_by_domain(domain)
        
        # Assertions
        assert result == tenant
        tenant_service._fetch_tenant_by_domain.assert_called_once_with(domain)
    
    async def test_update_tenant_success(self, tenant_service, sample_tenant_update):
        """Test successful tenant update."""
        tenant_id = "test-tenant-id"
        existing_tenant = MagicMock()
        existing_tenant.id = tenant_id
        existing_tenant.name = "Old Name"
        existing_tenant.description = "Old Description"
        existing_tenant.status = TenantStatus.ACTIVE
        
        # Mock get tenant
        tenant_service.get_tenant = AsyncMock(return_value=existing_tenant)
        tenant_service._store_tenant = AsyncMock()
        tenant_service._log_audit_event = AsyncMock()
        
        # Update tenant
        result = await tenant_service.update_tenant(
            tenant_id, sample_tenant_update, "admin-user-id"
        )
        
        # Assertions
        assert result.name == sample_tenant_update.name
        assert result.description == sample_tenant_update.description
        assert result.status == sample_tenant_update.status
        
        # Verify mocks were called
        tenant_service._store_tenant.assert_called_once()
        tenant_service._log_audit_event.assert_called_once()
    
    async def test_update_tenant_not_found(self, tenant_service, sample_tenant_update):
        """Test updating non-existent tenant."""
        tenant_id = "non-existent-tenant"
        
        # Mock get tenant to return None
        tenant_service.get_tenant = AsyncMock(return_value=None)
        
        # Attempt to update tenant
        with pytest.raises(TenantNotFoundError) as exc_info:
            await tenant_service.update_tenant(
                tenant_id, sample_tenant_update, "admin-user-id"
            )
        
        assert tenant_id in str(exc_info.value)
    
    async def test_delete_tenant_success(self, tenant_service):
        """Test successful tenant deletion."""
        tenant_id = "test-tenant-id"
        existing_tenant = MagicMock()
        existing_tenant.id = tenant_id
        existing_tenant.name = "Test Tenant"
        existing_tenant.domain = "test-domain"
        
        # Mock dependencies
        tenant_service.get_tenant = AsyncMock(return_value=existing_tenant)
        tenant_service._archive_tenant_data = AsyncMock()
        tenant_service._cleanup_tenant_resources = AsyncMock()
        tenant_service._delete_tenant_from_db = AsyncMock()
        tenant_service._log_audit_event = AsyncMock()
        
        # Delete tenant
        result = await tenant_service.delete_tenant(tenant_id, "admin-user-id")
        
        # Assertions
        assert result is True
        
        # Verify mocks were called
        tenant_service._archive_tenant_data.assert_called_once_with(tenant_id)
        tenant_service._cleanup_tenant_resources.assert_called_once_with(tenant_id)
        tenant_service._delete_tenant_from_db.assert_called_once_with(tenant_id)
        tenant_service._log_audit_event.assert_called_once()
    
    async def test_delete_tenant_not_found(self, tenant_service):
        """Test deleting non-existent tenant."""
        tenant_id = "non-existent-tenant"
        
        # Mock get tenant to return None
        tenant_service.get_tenant = AsyncMock(return_value=None)
        
        # Attempt to delete tenant
        with pytest.raises(TenantNotFoundError) as exc_info:
            await tenant_service.delete_tenant(tenant_id, "admin-user-id")
        
        assert tenant_id in str(exc_info.value)
    
    async def test_list_tenants_no_filters(self, tenant_service):
        """Test listing tenants without filters."""
        # Setup cache with sample tenants
        tenant1 = MagicMock()
        tenant1.name = "Tenant 1"
        tenant1.domain = "tenant1"
        tenant1.status = TenantStatus.ACTIVE
        
        tenant2 = MagicMock()
        tenant2.name = "Tenant 2"
        tenant2.domain = "tenant2"
        tenant2.status = TenantStatus.SUSPENDED
        
        tenant_service._tenant_cache = {
            "tenant1": tenant1,
            "tenant2": tenant2
        }
        
        # List tenants
        result = await tenant_service.list_tenants(page=1, page_size=10)
        
        # Assertions
        assert result.total == 2
        assert len(result.tenants) == 2
        assert result.page == 1
        assert result.page_size == 10
    
    async def test_list_tenants_with_status_filter(self, tenant_service):
        """Test listing tenants with status filter."""
        # Setup cache with sample tenants
        tenant1 = MagicMock()
        tenant1.status = TenantStatus.ACTIVE
        
        tenant2 = MagicMock()
        tenant2.status = TenantStatus.SUSPENDED
        
        tenant_service._tenant_cache = {
            "tenant1": tenant1,
            "tenant2": tenant2
        }
        
        # List active tenants only
        result = await tenant_service.list_tenants(
            page=1, page_size=10, status_filter=TenantStatus.ACTIVE
        )
        
        # Assertions
        assert result.total == 1
        assert len(result.tenants) == 1
        assert result.tenants[0].status == TenantStatus.ACTIVE
    
    async def test_list_tenants_with_search_query(self, tenant_service):
        """Test listing tenants with search query."""
        # Setup cache with sample tenants
        tenant1 = MagicMock()
        tenant1.name = "Production Tenant"
        tenant1.domain = "prod"
        tenant1.status = TenantStatus.ACTIVE
        
        tenant2 = MagicMock()
        tenant2.name = "Development Tenant"
        tenant2.domain = "dev"
        tenant2.status = TenantStatus.ACTIVE
        
        tenant_service._tenant_cache = {
            "tenant1": tenant1,
            "tenant2": tenant2
        }
        
        # Search for "prod"
        result = await tenant_service.list_tenants(
            page=1, page_size=10, search_query="prod"
        )
        
        # Assertions
        assert result.total == 1
        assert len(result.tenants) == 1
        assert "prod" in result.tenants[0].name.lower() or "prod" in result.tenants[0].domain.lower()
    
    async def test_get_tenant_stats_success(self, tenant_service):
        """Test getting tenant statistics."""
        tenant_id = "test-tenant-id"
        existing_tenant = MagicMock()
        existing_tenant.id = tenant_id
        
        # Mock dependencies
        tenant_service.get_tenant = AsyncMock(return_value=existing_tenant)
        tenant_service._get_user_count = AsyncMock(return_value=10)
        tenant_service._get_dashboard_count = AsyncMock(return_value=25)
        tenant_service._get_active_alert_count = AsyncMock(return_value=3)
        tenant_service._get_storage_usage = AsyncMock(return_value=1024.5)
        tenant_service._get_monthly_cost = AsyncMock(return_value=150.75)
        tenant_service._get_cost_trend = AsyncMock(return_value="up")
        tenant_service._get_last_activity = AsyncMock(return_value=datetime.utcnow())
        
        # Get tenant stats
        result = await tenant_service.get_tenant_stats(tenant_id)
        
        # Assertions
        assert result.tenant_id == tenant_id
        assert result.user_count == 10
        assert result.dashboard_count == 25
        assert result.alert_count == 3
        assert result.storage_usage_mb == 1024.5
        assert result.monthly_cost == 150.75
        assert result.cost_trend == "up"
        assert result.last_activity is not None
    
    async def test_get_tenant_stats_not_found(self, tenant_service):
        """Test getting stats for non-existent tenant."""
        tenant_id = "non-existent-tenant"
        
        # Mock get tenant to return None
        tenant_service.get_tenant = AsyncMock(return_value=None)
        
        # Attempt to get stats
        with pytest.raises(TenantNotFoundError) as exc_info:
            await tenant_service.get_tenant_stats(tenant_id)
        
        assert tenant_id in str(exc_info.value)
    
    async def test_get_tenant_health_success(self, tenant_service):
        """Test getting tenant health check."""
        tenant_id = "test-tenant-id"
        existing_tenant = MagicMock()
        existing_tenant.id = tenant_id
        
        # Mock dependencies
        tenant_service.get_tenant = AsyncMock(return_value=existing_tenant)
        tenant_service._check_prometheus_health = AsyncMock(return_value="healthy")
        tenant_service._check_loki_health = AsyncMock(return_value="healthy")
        tenant_service._check_tempo_health = AsyncMock(return_value="degraded")
        tenant_service._check_grafana_health = AsyncMock(return_value="healthy")
        tenant_service._check_opencost_health = AsyncMock(return_value="healthy")
        tenant_service._check_storage_health = AsyncMock(return_value={"status": "healthy"})
        tenant_service._check_cost_health = AsyncMock(return_value={"status": "healthy"})
        
        # Get tenant health
        result = await tenant_service.get_tenant_health(tenant_id)
        
        # Assertions
        assert result.tenant_id == tenant_id
        assert result.status == "degraded"  # Because tempo is degraded
        assert result.services["prometheus"] == "healthy"
        assert result.services["loki"] == "healthy"
        assert result.services["tempo"] == "degraded"
        assert result.services["grafana"] == "healthy"
        assert result.services["opencost"] == "healthy"
        assert len(result.issues) == 1
        assert "tempo: degraded" in result.issues
    
    async def test_cache_expiry(self, tenant_service):
        """Test cache expiry functionality."""
        tenant_id = "test-tenant-id"
        
        # Add tenant to cache with old timestamp
        old_time = datetime.utcnow() - timedelta(hours=1)
        tenant_service._tenant_cache[tenant_id] = MagicMock()
        tenant_service._last_cache_update[tenant_id] = old_time
        
        # Check if cached (should be False due to expiry)
        is_cached = tenant_service._is_cached(tenant_id)
        
        # Assertions
        assert is_cached is False
    
    async def test_cache_valid(self, tenant_service):
        """Test valid cache functionality."""
        tenant_id = "test-tenant-id"
        
        # Add tenant to cache with recent timestamp
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        tenant_service._tenant_cache[tenant_id] = MagicMock()
        tenant_service._last_cache_update[tenant_id] = recent_time
        
        # Check if cached (should be True)
        is_cached = tenant_service._is_cached(tenant_id)
        
        # Assertions
        assert is_cached is True