"""Tenant management API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from ...auth.dependencies import get_current_user, require_admin
from ...auth.models import UserContext
from ...models.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantList, TenantStats,
    TenantHealthCheck, TenantStatus, TenantAuditLogList
)
from ...services.tenant_service import TenantService
from ...exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError, TenantOperationError,
    ValidationError, AuthorizationError
)

router = APIRouter(prefix="/tenants", tags=["tenant-management"])


def get_tenant_service() -> TenantService:
    """Dependency to get tenant service instance."""
    return TenantService()


@router.post("", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> Tenant:
    """
    Create a new tenant with initial configuration.
    
    Requires admin role to create tenants.
    
    Args:
        tenant_data: Tenant creation data including name, domain, and settings
        current_user: Authenticated admin user
        tenant_service: Tenant service dependency
        
    Returns:
        Created tenant object with generated ID and timestamps
        
    Raises:
        HTTPException: 400 for validation errors, 409 for domain conflicts, 500 for creation errors
    """
    try:
        tenant = await tenant_service.create_tenant(tenant_data, current_user.user_id)
        return tenant
        
    except TenantAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TenantOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("", response_model=TenantList)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[TenantStatus] = Query(None, description="Filter by tenant status"),
    search: Optional[str] = Query(None, description="Search in tenant name or domain"),
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> TenantList:
    """
    List tenants with pagination and filtering.
    
    Requires admin role to list all tenants.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page (1-100)
        status: Filter by tenant status
        search: Search query for tenant name or domain
        current_user: Authenticated admin user
        tenant_service: Tenant service dependency
        
    Returns:
        Paginated list of tenants with metadata
    """
    try:
        tenant_list = await tenant_service.list_tenants(
            page=page,
            page_size=page_size,
            status_filter=status,
            search_query=search
        )
        return tenant_list
        
    except TenantOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant(
    tenant_id: str,
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> Tenant:
    """
    Get tenant details by ID.
    
    Requires admin role to view tenant details.
    
    Args:
        tenant_id: Tenant identifier
        current_user: Authenticated admin user
        tenant_service: Tenant service dependency
        
    Returns:
        Tenant object with full details
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    try:
        tenant = await tenant_service.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        return tenant
        
    except TenantOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: str,
    update_data: TenantUpdate,
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> Tenant:
    """
    Update tenant configuration.
    
    Requires admin role to update tenant settings.
    
    Args:
        tenant_id: Tenant identifier
        update_data: Tenant update data
        current_user: Authenticated admin user
        tenant_service: Tenant service dependency
        
    Returns:
        Updated tenant object
        
    Raises:
        HTTPException: 404 if tenant not found, 400 for validation errors
    """
    try:
        tenant = await tenant_service.update_tenant(
            tenant_id, update_data, current_user.user_id
        )
        return tenant
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TenantOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> None:
    """
    Delete tenant and all associated data.
    
    Requires admin role to delete tenants.
    WARNING: This operation is irreversible and will delete all tenant data.
    
    Args:
        tenant_id: Tenant identifier
        current_user: Authenticated admin user
        tenant_service: Tenant service dependency
        
    Raises:
        HTTPException: 404 if tenant not found, 500 for deletion errors
    """
    try:
        await tenant_service.delete_tenant(tenant_id, current_user.user_id)
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TenantOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(
    tenant_id: str,
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> TenantStats:
    """
    Get tenant statistics and usage metrics.
    
    Requires admin role to view tenant statistics.
    
    Args:
        tenant_id: Tenant identifier
        current_user: Authenticated admin user
        tenant_service: Tenant service dependency
        
    Returns:
        Tenant statistics including user count, storage usage, and costs
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    try:
        stats = await tenant_service.get_tenant_stats(tenant_id)
        return stats
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TenantOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{tenant_id}/health", response_model=TenantHealthCheck)
async def get_tenant_health(
    tenant_id: str,
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> TenantHealthCheck:
    """
    Check tenant health status across all services.
    
    Requires admin role to view tenant health.
    
    Args:
        tenant_id: Tenant identifier
        current_user: Authenticated admin user
        tenant_service: Tenant service dependency
        
    Returns:
        Tenant health check results including service status and issues
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    try:
        health = await tenant_service.get_tenant_health(tenant_id)
        return health
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TenantOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/domain/{domain}", response_model=Tenant)
async def get_tenant_by_domain(
    domain: str,
    current_user: UserContext = Depends(get_current_user),
    _: None = Depends(require_admin),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> Tenant:
    """
    Get tenant by domain identifier.
    
    Requires admin role to lookup tenants by domain.
    
    Args:
        domain: Tenant domain identifier
        current_user: Authenticated admin user
        tenant_service: Tenant service dependency
        
    Returns:
        Tenant object matching the domain
        
    Raises:
        HTTPException: 404 if tenant not found
    """
    try:
        tenant = await tenant_service.get_tenant_by_domain(domain)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with domain '{domain}' not found"
            )
        return tenant
        
    except TenantOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )