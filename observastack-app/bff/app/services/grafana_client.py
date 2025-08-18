"""Grafana client for proxy operations and dashboard management."""

import os
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse, parse_qs
import httpx
from fastapi import HTTPException, status

from ..auth.models import UserContext
from ..exceptions import GrafanaError

logger = logging.getLogger(__name__)


class GrafanaClient:
    """Client for interacting with Grafana API and proxying requests."""
    
    def __init__(
        self,
        base_url: str = None,
        admin_user: str = None,
        admin_password: str = None,
        timeout: int = 30
    ):
        """Initialize Grafana client."""
        self.base_url = base_url or os.getenv("GRAFANA_URL", "http://localhost:3000")
        self.admin_user = admin_user or os.getenv("GRAFANA_ADMIN_USER", "admin")
        self.admin_password = admin_password or os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")
        self.timeout = timeout
        
        # Remove trailing slash from base URL
        self.base_url = self.base_url.rstrip('/')
        
        # Initialize HTTP client with basic auth for admin operations
        self.client = httpx.AsyncClient(
            auth=(self.admin_user, self.admin_password),
            timeout=httpx.Timeout(timeout),
            follow_redirects=True
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if Grafana is healthy and accessible."""
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Grafana health check failed: {e}")
            return False
    
    async def create_service_account(self, name: str, role: str = "Viewer") -> Dict[str, Any]:
        """Create a service account for tenant isolation."""
        try:
            payload = {
                "name": name,
                "role": role,
                "isDisabled": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/serviceaccounts",
                json=payload
            )
            
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 409:
                # Service account already exists, get it
                return await self.get_service_account_by_name(name)
            else:
                raise GrafanaError(f"Failed to create service account: {response.text}")
                
        except httpx.RequestError as e:
            raise GrafanaError(f"Request failed: {str(e)}")
    
    async def get_service_account_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service account by name."""
        try:
            response = await self.client.get(f"{self.base_url}/api/serviceaccounts/search?query={name}")
            
            if response.status_code == 200:
                accounts = response.json().get("serviceAccounts", [])
                for account in accounts:
                    if account.get("name") == name:
                        return account
                return None
            else:
                raise GrafanaError(f"Failed to search service accounts: {response.text}")
                
        except httpx.RequestError as e:
            raise GrafanaError(f"Request failed: {str(e)}")
    
    async def create_service_account_token(self, service_account_id: int, name: str) -> str:
        """Create a token for a service account."""
        try:
            payload = {
                "name": name,
                "role": "Viewer"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/serviceaccounts/{service_account_id}/tokens",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json().get("key", "")
            else:
                raise GrafanaError(f"Failed to create service account token: {response.text}")
                
        except httpx.RequestError as e:
            raise GrafanaError(f"Request failed: {str(e)}")
    
    async def get_or_create_tenant_token(self, tenant_id: str) -> str:
        """Get or create a service account token for a tenant."""
        service_account_name = f"tenant-{tenant_id}"
        token_name = f"token-{tenant_id}"
        
        # Get or create service account
        service_account = await self.create_service_account(service_account_name)
        service_account_id = service_account.get("id")
        
        if not service_account_id:
            raise GrafanaError("Failed to get service account ID")
        
        # Create token for the service account
        token = await self.create_service_account_token(service_account_id, token_name)
        
        if not token:
            raise GrafanaError("Failed to create service account token")
        
        return token
    
    async def proxy_request(
        self,
        method: str,
        path: str,
        user_context: UserContext,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """
        Proxy a request to Grafana with tenant-aware authentication.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Grafana API path (e.g., '/api/dashboards/home')
            user_context: User context for tenant isolation
            params: Query parameters
            json_data: JSON payload for POST/PUT requests
            headers: Additional headers
            
        Returns:
            httpx.Response: Grafana response
        """
        try:
            # Get tenant-specific token
            tenant_token = await self.get_or_create_tenant_token(user_context.tenant_id)
            
            # Prepare headers with tenant token
            request_headers = {
                "Authorization": f"Bearer {tenant_token}",
                "Content-Type": "application/json",
                "X-Tenant-ID": user_context.tenant_id,
                "X-User-ID": user_context.user_id
            }
            
            if headers:
                request_headers.update(headers)
            
            # Build full URL
            url = f"{self.base_url}{path}"
            
            # Add tenant isolation to query parameters
            if params is None:
                params = {}
            
            # Add tenant context to certain API calls
            if self._requires_tenant_filter(path):
                params = self._add_tenant_filters(params, user_context.tenant_id)
            
            # Make the request
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers
            )
            
            return response
            
        except httpx.RequestError as e:
            logger.error(f"Grafana proxy request failed: {e}")
            raise GrafanaError(f"Proxy request failed: {str(e)}")
    
    def _requires_tenant_filter(self, path: str) -> bool:
        """Check if the API path requires tenant filtering."""
        tenant_filtered_paths = [
            "/api/search",
            "/api/dashboards",
            "/api/annotations",
            "/api/alerts",
            "/api/datasources/proxy"
        ]
        
        return any(path.startswith(filtered_path) for filtered_path in tenant_filtered_paths)
    
    def _add_tenant_filters(self, params: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Add tenant isolation filters to query parameters."""
        # Add tenant tag filter for searches and queries
        if "tag" not in params:
            params["tag"] = []
        elif isinstance(params["tag"], str):
            params["tag"] = [params["tag"]]
        
        # Add tenant tag
        if isinstance(params["tag"], list):
            params["tag"].append(f"tenant:{tenant_id}")
        
        return params
    
    async def get_dashboard_url(
        self,
        dashboard_uid: str,
        user_context: UserContext,
        panel_id: Optional[int] = None,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        refresh: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate a dashboard URL with tenant context and authentication.
        
        Args:
            dashboard_uid: Dashboard UID
            user_context: User context for tenant isolation
            panel_id: Optional panel ID for direct panel linking
            time_from: Optional time range start
            time_to: Optional time range end
            refresh: Optional refresh interval
            variables: Optional dashboard variables
            
        Returns:
            str: Complete dashboard URL with authentication and parameters
        """
        # Get tenant-specific token
        tenant_token = await self.get_or_create_tenant_token(user_context.tenant_id)
        
        # Build base URL
        if panel_id:
            base_path = f"/d-solo/{dashboard_uid}"
        else:
            base_path = f"/d/{dashboard_uid}"
        
        # Build query parameters
        params = {
            "auth_token": tenant_token,
            "tenant": user_context.tenant_id
        }
        
        if panel_id:
            params["panelId"] = str(panel_id)
        
        if time_from:
            params["from"] = time_from
        
        if time_to:
            params["to"] = time_to
        
        if refresh:
            params["refresh"] = refresh
        
        # Add dashboard variables
        if variables:
            for key, value in variables.items():
                params[f"var-{key}"] = value
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        return f"{self.base_url}{base_path}?{query_string}"
    
    async def get_dashboards_for_tenant(self, user_context: UserContext) -> List[Dict[str, Any]]:
        """Get all dashboards accessible to a tenant."""
        try:
            response = await self.proxy_request(
                method="GET",
                path="/api/search",
                user_context=user_context,
                params={"type": "dash-db"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise GrafanaError(f"Failed to get dashboards: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to get tenant dashboards: {e}")
            raise GrafanaError(f"Failed to get dashboards: {str(e)}")
    
    async def get_dashboard_by_uid(
        self,
        dashboard_uid: str,
        user_context: UserContext
    ) -> Dict[str, Any]:
        """Get a specific dashboard by UID."""
        try:
            response = await self.proxy_request(
                method="GET",
                path=f"/api/dashboards/uid/{dashboard_uid}",
                user_context=user_context
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dashboard {dashboard_uid} not found"
                )
            else:
                raise GrafanaError(f"Failed to get dashboard: {response.text}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get dashboard {dashboard_uid}: {e}")
            raise GrafanaError(f"Failed to get dashboard: {str(e)}")
    
    async def create_dashboard_snapshot(
        self,
        dashboard_uid: str,
        user_context: UserContext,
        expires: int = 3600
    ) -> Dict[str, Any]:
        """Create a dashboard snapshot for sharing."""
        try:
            # Get the dashboard first
            dashboard = await self.get_dashboard_by_uid(dashboard_uid, user_context)
            
            payload = {
                "dashboard": dashboard.get("dashboard", {}),
                "expires": expires,
                "external": False,
                "key": "",
                "name": f"Snapshot for {dashboard_uid}",
                "orgId": 1
            }
            
            response = await self.proxy_request(
                method="POST",
                path="/api/snapshots",
                user_context=user_context,
                json_data=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise GrafanaError(f"Failed to create snapshot: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to create dashboard snapshot: {e}")
            raise GrafanaError(f"Failed to create snapshot: {str(e)}")
    
    def get_embed_url(
        self,
        dashboard_uid: str,
        panel_id: Optional[int] = None,
        theme: str = "light",
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate an embed URL for iframe integration.
        
        Args:
            dashboard_uid: Dashboard UID
            panel_id: Optional panel ID for single panel embed
            theme: Theme (light/dark)
            time_from: Optional time range start
            time_to: Optional time range end
            variables: Optional dashboard variables
            
        Returns:
            str: Embed URL for iframe
        """
        if panel_id:
            base_path = f"/d-solo/{dashboard_uid}"
        else:
            base_path = f"/d/{dashboard_uid}"
        
        params = {
            "orgId": "1",
            "theme": theme,
            "kiosk": "true"
        }
        
        if panel_id:
            params["panelId"] = str(panel_id)
        
        if time_from:
            params["from"] = time_from
        
        if time_to:
            params["to"] = time_to
        
        # Add dashboard variables
        if variables:
            for key, value in variables.items():
                params[f"var-{key}"] = value
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        return f"{self.base_url}{base_path}?{query_string}"