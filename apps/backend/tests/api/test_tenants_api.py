"""Unit tests for tenant management API endpoints."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.models.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantList, TenantStats,
    TenantHealthCheck, TenantStatus, TenantSettings, DataRetentionPolicy
)
from app.exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError, TenantOperationError
)


class TestTenantAPI:
    """Test cases for tenant management API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def admin_headers(self):
        """Mock admin authentication headers."""
        return {"Authorization": "Bearer admin-token"}
    
    @pytest.fixture
    def sample_tenant(self):
        """Sample tenant object."""
        return Tenant(
            id="test-tenant-id",
            name="Test Tenant",
            domain="test-tenant",
            description="A test tenant",
            status=TenantStatus.ACTIVE,
            settings=TenantSettings(),
            retention_policy=DataRetentionPolicy(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            user_count=5,
            storage_usage_mb=1024.0
        )
    
    @pytest.fixture
    def sample_tenant_create(self):
        """Sample tenant creation data."""
        return {
            "name": "New Tenant",
            "domain": "new-tenant",
            "description": "A new test tenant",
            "admin_email": "admin@newtest.com",
            "admin_username": "newadmin",
            "settings": {
                "max_users": 50,
                "max_dashboards": 100,
                "features_enabled": ["search", "alerts"]
            }
        }
    
    @pytest.fixture
    def sample_tenant_update(self):
        """Sample tenant update data."""
        return {
            "name": "Updated Tenant",
            "description": "Updated description",
            "status": "suspended"
        }
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_create_tenant_success(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant_create, sample_tenant
    ):
        """Test successful tenant creation."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.create_tenant.return_value = sample_tenant
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/tenants",
            json=sample_tenant_create,
            headers=admin_headers
        )
        
        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == sample_tenant.id
        assert data["name"] == sample_tenant.name
        assert data["domain"] == sample_tenant.domain
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_create_tenant_domain_conflict(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant_create
    ):
        """Test tenant creation with domain conflict."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.create_tenant.side_effect = TenantAlreadyExistsError("Domain already exists")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/tenants",
            json=sample_tenant_create,
            headers=admin_headers
        )
        
        # Assertions
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "already exists" in data["detail"]
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_list_tenants_success(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant
    ):
        """Test successful tenant listing."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        tenant_list = TenantList(
            tenants=[sample_tenant],
            total=1,
            page=1,
            page_size=20
        )
        
        mock_service = AsyncMock()
        mock_service.list_tenants.return_value = tenant_list
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/tenants", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["tenants"]) == 1
        assert data["tenants"][0]["id"] == sample_tenant.id
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_list_tenants_with_filters(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers
    ):
        """Test tenant listing with filters."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.list_tenants.return_value = TenantList(
            tenants=[], total=0, page=1, page_size=20
        )
        mock_get_service.return_value = mock_service
        
        # Make request with filters
        response = client.get(
            "/api/v1/tenants?page=2&page_size=10&status=active&search=test",
            headers=admin_headers
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        
        # Verify service was called with correct parameters
        mock_service.list_tenants.assert_called_once_with(
            page=2,
            page_size=10,
            status_filter=TenantStatus.ACTIVE,
            search_query="test"
        )
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_get_tenant_success(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant
    ):
        """Test successful tenant retrieval."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.get_tenant.return_value = sample_tenant
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(f"/api/v1/tenants/{sample_tenant.id}", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_tenant.id
        assert data["name"] == sample_tenant.name
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_get_tenant_not_found(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers
    ):
        """Test tenant retrieval when tenant not found."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.get_tenant.return_value = None
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/tenants/non-existent", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"]
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_update_tenant_success(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant, sample_tenant_update
    ):
        """Test successful tenant update."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        updated_tenant = sample_tenant.copy()
        updated_tenant.name = sample_tenant_update["name"]
        updated_tenant.description = sample_tenant_update["description"]
        updated_tenant.status = TenantStatus.SUSPENDED
        
        mock_service = AsyncMock()
        mock_service.update_tenant.return_value = updated_tenant
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.put(
            f"/api/v1/tenants/{sample_tenant.id}",
            json=sample_tenant_update,
            headers=admin_headers
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == sample_tenant_update["name"]
        assert data["description"] == sample_tenant_update["description"]
        assert data["status"] == "suspended"
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_update_tenant_not_found(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant_update
    ):
        """Test tenant update when tenant not found."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.update_tenant.side_effect = TenantNotFoundError("Tenant not found")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.put(
            "/api/v1/tenants/non-existent",
            json=sample_tenant_update,
            headers=admin_headers
        )
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"]
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_delete_tenant_success(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant
    ):
        """Test successful tenant deletion."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.delete_tenant.return_value = True
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.delete(f"/api/v1/tenants/{sample_tenant.id}", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_delete_tenant_not_found(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers
    ):
        """Test tenant deletion when tenant not found."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.delete_tenant.side_effect = TenantNotFoundError("Tenant not found")
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.delete("/api/v1/tenants/non-existent", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"]
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_get_tenant_stats_success(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant
    ):
        """Test successful tenant stats retrieval."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        tenant_stats = TenantStats(
            tenant_id=sample_tenant.id,
            user_count=10,
            dashboard_count=25,
            alert_count=3,
            storage_usage_mb=1024.5,
            monthly_cost=150.75,
            cost_trend="up",
            last_activity=datetime.utcnow()
        )
        
        mock_service = AsyncMock()
        mock_service.get_tenant_stats.return_value = tenant_stats
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(f"/api/v1/tenants/{sample_tenant.id}/stats", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tenant_id"] == sample_tenant.id
        assert data["user_count"] == 10
        assert data["dashboard_count"] == 25
        assert data["monthly_cost"] == 150.75
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_get_tenant_health_success(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant
    ):
        """Test successful tenant health check."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        tenant_health = TenantHealthCheck(
            tenant_id=sample_tenant.id,
            status="healthy",
            services={
                "prometheus": "healthy",
                "loki": "healthy",
                "tempo": "healthy",
                "grafana": "healthy",
                "opencost": "healthy"
            },
            storage_health={"status": "healthy", "usage_percent": 45.2},
            cost_health={"status": "healthy", "budget_usage_percent": 65.0},
            last_check=datetime.utcnow(),
            issues=[]
        )
        
        mock_service = AsyncMock()
        mock_service.get_tenant_health.return_value = tenant_health
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(f"/api/v1/tenants/{sample_tenant.id}/health", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tenant_id"] == sample_tenant.id
        assert data["status"] == "healthy"
        assert data["services"]["prometheus"] == "healthy"
        assert len(data["issues"]) == 0
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_get_tenant_by_domain_success(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers, sample_tenant
    ):
        """Test successful tenant retrieval by domain."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.get_tenant_by_domain.return_value = sample_tenant
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(f"/api/v1/tenants/domain/{sample_tenant.domain}", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_tenant.id
        assert data["domain"] == sample_tenant.domain
    
    @patch('app.api.v1.tenants.get_current_user')
    @patch('app.api.v1.tenants.require_admin')
    @patch('app.api.v1.tenants.get_tenant_service')
    def test_get_tenant_by_domain_not_found(
        self, mock_get_service, mock_require_admin, mock_get_user,
        client, admin_headers
    ):
        """Test tenant retrieval by domain when not found."""
        # Mock dependencies
        mock_get_user.return_value = MagicMock(user_id="admin-user-id")
        mock_require_admin.return_value = None
        
        mock_service = AsyncMock()
        mock_service.get_tenant_by_domain.return_value = None
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get("/api/v1/tenants/domain/non-existent", headers=admin_headers)
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_create_tenant_validation_error(self, client, admin_headers):
        """Test tenant creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "domain": "invalid domain!",  # Invalid domain format
            "admin_email": "invalid-email"  # Invalid email format
        }
        
        # Make request
        response = client.post(
            "/api/v1/tenants",
            json=invalid_data,
            headers=admin_headers
        )
        
        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to tenant endpoints."""
        # Make request without authentication
        response = client.get("/api/v1/tenants")
        
        # Assertions
        assert response.status_code == status.HTTP_401_UNAUTHORIZED