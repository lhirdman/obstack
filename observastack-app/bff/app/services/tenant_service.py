"""Tenant management service for multi-tenant operations."""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

# Optional SQLAlchemy imports for database operations
try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, update, delete, func, and_, or_
    HAS_SQLALCHEMY = True
except ImportError:
    AsyncSession = None
    HAS_SQLALCHEMY = False

from ..models.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantList, TenantStats,
    TenantUsageMetrics, TenantAuditLog, TenantAuditLogList,
    TenantHealthCheck, TenantStatus, DataRetentionPolicy, TenantSettings
)
from ..exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError, TenantOperationError,
    ValidationError, AuthorizationError
)

logger = logging.getLogger(__name__)


class TenantService:
    """Service for managing tenant operations and multi-tenant isolation."""
    
    def __init__(self, db_session=None):
        """
        Initialize tenant service.
        
        Args:
            db_session: Database session for persistence operations (optional)
        """
        self.db_session = db_session
        self._tenant_cache: Dict[str, Tenant] = {}
        self._cache_ttl = timedelta(minutes=15)
        self._last_cache_update: Dict[str, datetime] = {}
    
    async def create_tenant(
        self, 
        tenant_data: TenantCreate, 
        created_by: str
    ) -> Tenant:
        """
        Create a new tenant with initial configuration.
        
        Args:
            tenant_data: Tenant creation data
            created_by: User ID who is creating the tenant
            
        Returns:
            Created tenant object
            
        Raises:
            TenantAlreadyExistsError: If tenant domain already exists
            ValidationError: If tenant data is invalid
        """
        try:
            # Check if tenant domain already exists
            if await self._domain_exists(tenant_data.domain):
                raise TenantAlreadyExistsError(f"Tenant domain '{tenant_data.domain}' already exists")
            
            # Generate unique tenant ID
            tenant_id = str(uuid.uuid4())
            
            # Create tenant object
            now = datetime.utcnow()
            tenant = Tenant(
                id=tenant_id,
                name=tenant_data.name,
                domain=tenant_data.domain,
                description=tenant_data.description,
                status=TenantStatus.ACTIVE,
                settings=tenant_data.settings or TenantSettings(),
                retention_policy=tenant_data.retention_policy or DataRetentionPolicy(),
                created_at=now,
                updated_at=now,
                user_count=0,
                storage_usage_mb=0.0
            )
            
            # Store tenant in database (mock implementation)
            await self._store_tenant(tenant)
            
            # Create initial admin user for tenant
            await self._create_tenant_admin(
                tenant_id=tenant_id,
                admin_email=tenant_data.admin_email,
                admin_username=tenant_data.admin_username
            )
            
            # Log tenant creation
            await self._log_audit_event(
                tenant_id=tenant_id,
                user_id=created_by,
                action="tenant_created",
                resource_type="tenant",
                resource_id=tenant_id,
                details={
                    "tenant_name": tenant_data.name,
                    "tenant_domain": tenant_data.domain,
                    "admin_email": tenant_data.admin_email
                }
            )
            
            # Initialize tenant resources
            await self._initialize_tenant_resources(tenant_id)
            
            logger.info(f"Created tenant {tenant_id} with domain {tenant_data.domain}")
            return tenant
            
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            if isinstance(e, (TenantAlreadyExistsError, ValidationError)):
                raise
            raise TenantOperationError(f"Failed to create tenant: {str(e)}")
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get tenant by ID with caching.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tenant object or None if not found
        """
        try:
            # Check cache first
            if self._is_cached(tenant_id):
                return self._tenant_cache[tenant_id]
            
            # Fetch from database (mock implementation)
            tenant = await self._fetch_tenant_by_id(tenant_id)
            
            if tenant:
                # Update cache
                self._tenant_cache[tenant_id] = tenant
                self._last_cache_update[tenant_id] = datetime.utcnow()
            
            return tenant
            
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            return None
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """
        Get tenant by domain identifier.
        
        Args:
            domain: Tenant domain
            
        Returns:
            Tenant object or None if not found
        """
        try:
            # Mock implementation - would query database
            for tenant in self._tenant_cache.values():
                if tenant.domain == domain:
                    return tenant
            
            # Fetch from database
            tenant = await self._fetch_tenant_by_domain(domain)
            
            if tenant:
                # Update cache
                self._tenant_cache[tenant.id] = tenant
                self._last_cache_update[tenant.id] = datetime.utcnow()
            
            return tenant
            
        except Exception as e:
            logger.error(f"Failed to get tenant by domain {domain}: {e}")
            return None
    
    async def update_tenant(
        self, 
        tenant_id: str, 
        update_data: TenantUpdate, 
        updated_by: str
    ) -> Tenant:
        """
        Update tenant configuration.
        
        Args:
            tenant_id: Tenant identifier
            update_data: Update data
            updated_by: User ID performing the update
            
        Returns:
            Updated tenant object
            
        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")
            
            # Track changes for audit log
            changes = {}
            
            # Update fields
            if update_data.name is not None:
                changes["name"] = {"old": tenant.name, "new": update_data.name}
                tenant.name = update_data.name
            
            if update_data.description is not None:
                changes["description"] = {"old": tenant.description, "new": update_data.description}
                tenant.description = update_data.description
            
            if update_data.status is not None:
                changes["status"] = {"old": tenant.status, "new": update_data.status}
                tenant.status = update_data.status
            
            if update_data.settings is not None:
                changes["settings"] = {"old": tenant.settings.dict(), "new": update_data.settings.dict()}
                tenant.settings = update_data.settings
            
            if update_data.retention_policy is not None:
                changes["retention_policy"] = {
                    "old": tenant.retention_policy.dict(), 
                    "new": update_data.retention_policy.dict()
                }
                tenant.retention_policy = update_data.retention_policy
            
            tenant.updated_at = datetime.utcnow()
            
            # Store updated tenant
            await self._store_tenant(tenant)
            
            # Update cache
            self._tenant_cache[tenant_id] = tenant
            self._last_cache_update[tenant_id] = datetime.utcnow()
            
            # Log update
            await self._log_audit_event(
                tenant_id=tenant_id,
                user_id=updated_by,
                action="tenant_updated",
                resource_type="tenant",
                resource_id=tenant_id,
                details={"changes": changes}
            )
            
            logger.info(f"Updated tenant {tenant_id}")
            return tenant
            
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}")
            if isinstance(e, TenantNotFoundError):
                raise
            raise TenantOperationError(f"Failed to update tenant: {str(e)}")
    
    async def delete_tenant(self, tenant_id: str, deleted_by: str) -> bool:
        """
        Delete tenant and all associated data.
        
        Args:
            tenant_id: Tenant identifier
            deleted_by: User ID performing the deletion
            
        Returns:
            True if deletion was successful
            
        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")
            
            # Archive tenant data before deletion
            await self._archive_tenant_data(tenant_id)
            
            # Delete tenant resources
            await self._cleanup_tenant_resources(tenant_id)
            
            # Remove from database
            await self._delete_tenant_from_db(tenant_id)
            
            # Remove from cache
            self._tenant_cache.pop(tenant_id, None)
            self._last_cache_update.pop(tenant_id, None)
            
            # Log deletion
            await self._log_audit_event(
                tenant_id=tenant_id,
                user_id=deleted_by,
                action="tenant_deleted",
                resource_type="tenant",
                resource_id=tenant_id,
                details={"tenant_name": tenant.name, "tenant_domain": tenant.domain}
            )
            
            logger.info(f"Deleted tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            if isinstance(e, TenantNotFoundError):
                raise
            raise TenantOperationError(f"Failed to delete tenant: {str(e)}")
    
    async def list_tenants(
        self, 
        page: int = 1, 
        page_size: int = 20,
        status_filter: Optional[TenantStatus] = None,
        search_query: Optional[str] = None
    ) -> TenantList:
        """
        List tenants with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            status_filter: Filter by tenant status
            search_query: Search in tenant name or domain
            
        Returns:
            Paginated list of tenants
        """
        try:
            # Mock implementation - would query database with filters
            all_tenants = list(self._tenant_cache.values())
            
            # Apply filters
            if status_filter:
                all_tenants = [t for t in all_tenants if t.status == status_filter]
            
            if search_query:
                search_lower = search_query.lower()
                all_tenants = [
                    t for t in all_tenants 
                    if search_lower in t.name.lower() or search_lower in t.domain.lower()
                ]
            
            # Apply pagination
            total = len(all_tenants)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            tenants = all_tenants[start_idx:end_idx]
            
            return TenantList(
                tenants=tenants,
                total=total,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            raise TenantOperationError(f"Failed to list tenants: {str(e)}")
    
    async def get_tenant_stats(self, tenant_id: str) -> TenantStats:
        """
        Get tenant statistics and usage metrics.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tenant statistics
            
        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")
            
            # Mock implementation - would aggregate from various sources
            stats = TenantStats(
                tenant_id=tenant_id,
                user_count=await self._get_user_count(tenant_id),
                dashboard_count=await self._get_dashboard_count(tenant_id),
                alert_count=await self._get_active_alert_count(tenant_id),
                storage_usage_mb=await self._get_storage_usage(tenant_id),
                monthly_cost=await self._get_monthly_cost(tenant_id),
                cost_trend=await self._get_cost_trend(tenant_id),
                last_activity=await self._get_last_activity(tenant_id)
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get tenant stats for {tenant_id}: {e}")
            if isinstance(e, TenantNotFoundError):
                raise
            raise TenantOperationError(f"Failed to get tenant stats: {str(e)}")
    
    async def get_tenant_health(self, tenant_id: str) -> TenantHealthCheck:
        """
        Check tenant health status across all services.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tenant health check results
        """
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")
            
            # Check various service health
            services_health = {
                "prometheus": await self._check_prometheus_health(tenant_id),
                "loki": await self._check_loki_health(tenant_id),
                "tempo": await self._check_tempo_health(tenant_id),
                "grafana": await self._check_grafana_health(tenant_id),
                "opencost": await self._check_opencost_health(tenant_id)
            }
            
            storage_health = await self._check_storage_health(tenant_id)
            cost_health = await self._check_cost_health(tenant_id)
            
            # Determine overall status
            all_healthy = all(status == "healthy" for status in services_health.values())
            overall_status = "healthy" if all_healthy else "degraded"
            
            # Collect issues
            issues = []
            for service, status in services_health.items():
                if status != "healthy":
                    issues.append(f"{service}: {status}")
            
            return TenantHealthCheck(
                tenant_id=tenant_id,
                status=overall_status,
                services=services_health,
                storage_health=storage_health,
                cost_health=cost_health,
                last_check=datetime.utcnow(),
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Failed to check tenant health for {tenant_id}: {e}")
            if isinstance(e, TenantNotFoundError):
                raise
            raise TenantOperationError(f"Failed to check tenant health: {str(e)}")
    
    # Private helper methods
    
    def _is_cached(self, tenant_id: str) -> bool:
        """Check if tenant is cached and cache is still valid."""
        if tenant_id not in self._tenant_cache:
            return False
        
        last_update = self._last_cache_update.get(tenant_id)
        if not last_update:
            return False
        
        return datetime.utcnow() - last_update < self._cache_ttl
    
    async def _domain_exists(self, domain: str) -> bool:
        """Check if tenant domain already exists."""
        # Mock implementation - would query database
        return any(t.domain == domain for t in self._tenant_cache.values())
    
    async def _store_tenant(self, tenant: Tenant) -> None:
        """Store tenant in database."""
        # Mock implementation - would use actual database
        self._tenant_cache[tenant.id] = tenant
        self._last_cache_update[tenant.id] = datetime.utcnow()
    
    async def _fetch_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Fetch tenant from database by ID."""
        # Mock implementation - would query database
        return self._tenant_cache.get(tenant_id)
    
    async def _fetch_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Fetch tenant from database by domain."""
        # Mock implementation - would query database
        for tenant in self._tenant_cache.values():
            if tenant.domain == domain:
                return tenant
        return None
    
    async def _create_tenant_admin(self, tenant_id: str, admin_email: str, admin_username: str) -> None:
        """Create initial admin user for tenant."""
        # Mock implementation - would integrate with identity provider
        logger.info(f"Creating admin user {admin_username} for tenant {tenant_id}")
    
    async def _initialize_tenant_resources(self, tenant_id: str) -> None:
        """Initialize tenant-specific resources and configurations."""
        # Mock implementation - would set up tenant-specific resources
        logger.info(f"Initializing resources for tenant {tenant_id}")
    
    async def _log_audit_event(
        self, 
        tenant_id: str, 
        user_id: str, 
        action: str, 
        resource_type: str,
        resource_id: str = None,
        details: Dict[str, Any] = None
    ) -> None:
        """Log audit event for tenant operations."""
        # Mock implementation - would store in audit log
        logger.info(f"Audit: {action} on {resource_type} by {user_id} in tenant {tenant_id}")
    
    async def _archive_tenant_data(self, tenant_id: str) -> None:
        """Archive tenant data before deletion."""
        # Mock implementation - would archive data
        logger.info(f"Archiving data for tenant {tenant_id}")
    
    async def _cleanup_tenant_resources(self, tenant_id: str) -> None:
        """Clean up tenant-specific resources."""
        # Mock implementation - would clean up resources
        logger.info(f"Cleaning up resources for tenant {tenant_id}")
    
    async def _delete_tenant_from_db(self, tenant_id: str) -> None:
        """Delete tenant from database."""
        # Mock implementation - would delete from database
        self._tenant_cache.pop(tenant_id, None)
        self._last_cache_update.pop(tenant_id, None)
    
    # Mock metric collection methods
    
    async def _get_user_count(self, tenant_id: str) -> int:
        """Get number of users in tenant."""
        return 5  # Mock value
    
    async def _get_dashboard_count(self, tenant_id: str) -> int:
        """Get number of dashboards in tenant."""
        return 12  # Mock value
    
    async def _get_active_alert_count(self, tenant_id: str) -> int:
        """Get number of active alerts in tenant."""
        return 3  # Mock value
    
    async def _get_storage_usage(self, tenant_id: str) -> float:
        """Get storage usage in MB for tenant."""
        return 1024.5  # Mock value
    
    async def _get_monthly_cost(self, tenant_id: str) -> Optional[float]:
        """Get current monthly cost for tenant."""
        return 150.75  # Mock value
    
    async def _get_cost_trend(self, tenant_id: str) -> Optional[str]:
        """Get cost trend for tenant."""
        return "up"  # Mock value
    
    async def _get_last_activity(self, tenant_id: str) -> Optional[datetime]:
        """Get last user activity timestamp for tenant."""
        return datetime.utcnow() - timedelta(hours=2)  # Mock value
    
    # Mock health check methods
    
    async def _check_prometheus_health(self, tenant_id: str) -> str:
        """Check Prometheus health for tenant."""
        return "healthy"  # Mock value
    
    async def _check_loki_health(self, tenant_id: str) -> str:
        """Check Loki health for tenant."""
        return "healthy"  # Mock value
    
    async def _check_tempo_health(self, tenant_id: str) -> str:
        """Check Tempo health for tenant."""
        return "healthy"  # Mock value
    
    async def _check_grafana_health(self, tenant_id: str) -> str:
        """Check Grafana health for tenant."""
        return "healthy"  # Mock value
    
    async def _check_opencost_health(self, tenant_id: str) -> str:
        """Check OpenCost health for tenant."""
        return "healthy"  # Mock value
    
    async def _check_storage_health(self, tenant_id: str) -> Dict[str, Any]:
        """Check storage health for tenant."""
        return {
            "status": "healthy",
            "usage_percent": 45.2,
            "available_mb": 5000.0
        }
    
    async def _check_cost_health(self, tenant_id: str) -> Dict[str, Any]:
        """Check cost monitoring health for tenant."""
        return {
            "status": "healthy",
            "budget_usage_percent": 65.0,
            "alerts_active": 0
        }