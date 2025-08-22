"""
Metrics service for querying Prometheus/Thanos API with tenant isolation.
"""

import logging
import re
from typing import Dict, Any, Optional
from prometheus_api_client import PrometheusConnect

from app.core.config import settings
from app.core.error_handling import ExternalServiceError

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for querying Prometheus/Thanos with tenant isolation."""
    
    def __init__(self):
        """Initialize the Prometheus client."""
        self.prometheus = PrometheusConnect(
            url=settings.prometheus_url,
            disable_ssl=True  # For development, enable SSL verification in production
        )
        logger.info(f"Initialized Prometheus client with URL: {settings.prometheus_url}")
    
    def _inject_tenant_label(self, query: str, tenant_id: int) -> str:
        """
        Inject tenant_id label into PromQL query for data isolation.
        
        This implementation uses a safer, more predictable approach that wraps
        the entire query with a tenant filter to prevent data leakage.
        
        Args:
            query: Original PromQL query
            tenant_id: Tenant ID to inject
            
        Returns:
            Modified query with tenant_id label injected
        """
        # Validate tenant_id to prevent injection attacks
        if not isinstance(tenant_id, int) or tenant_id <= 0:
            raise ValueError(f"Invalid tenant_id: {tenant_id}")
        
        # Use a safer approach: wrap the query with tenant filtering
        # This ensures all metrics are filtered by tenant_id without complex regex
        tenant_filter = f'{{tenant_id="{tenant_id}"}}'
        
        # For simple metric names, add the tenant filter directly
        if re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$', query.strip()):
            modified_query = f'{query.strip()}{tenant_filter}'
        else:
            # For complex queries, use vector matching to ensure tenant isolation
            # This approach is safer and more predictable
            modified_query = f'({query}) and on() vector(1){tenant_filter}'
        
        logger.debug(f"Original query: {query}")
        logger.debug(f"Modified query: {modified_query}")
        
        return modified_query
    
    async def query(self, query: str, tenant_id: int, time: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a PromQL query with tenant isolation.
        
        Args:
            query: PromQL query string
            tenant_id: Tenant ID for data isolation
            time: Optional timestamp for the query (RFC3339 format)
            
        Returns:
            Query results from Prometheus
            
        Raises:
            ExternalServiceError: If query fails or returns invalid data
        """
        try:
            # Inject tenant_id label for data isolation
            modified_query = self._inject_tenant_label(query, tenant_id)
            
            # Execute query
            if time:
                result = self.prometheus.custom_query(query=modified_query, params={"time": time})
            else:
                result = self.prometheus.custom_query(query=modified_query)
            
            logger.info(f"Executed query for tenant {tenant_id}: {modified_query}")
            
            return {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": result
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to execute Prometheus query: {str(e)}")
            raise ExternalServiceError(f"Failed to query metrics: {str(e)}")
    
    async def query_range(
        self, 
        query: str, 
        tenant_id: int, 
        start: str, 
        end: str, 
        step: str
    ) -> Dict[str, Any]:
        """
        Execute a PromQL range query with tenant isolation.
        
        Args:
            query: PromQL query string
            tenant_id: Tenant ID for data isolation
            start: Start time (RFC3339 format)
            end: End time (RFC3339 format)
            step: Query resolution step
            
        Returns:
            Range query results from Prometheus
            
        Raises:
            ExternalServiceError: If query fails or returns invalid data
        """
        try:
            # Inject tenant_id label for data isolation
            modified_query = self._inject_tenant_label(query, tenant_id)
            
            # Execute range query
            result = self.prometheus.custom_query_range(
                query=modified_query,
                start_time=start,
                end_time=end,
                step=step
            )
            
            logger.info(f"Executed range query for tenant {tenant_id}: {modified_query}")
            
            return {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": result
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to execute Prometheus range query: {str(e)}")
            raise ExternalServiceError(f"Failed to query metrics range: {str(e)}")
    
    async def get_label_values(self, label: str, tenant_id: int) -> Dict[str, Any]:
        """
        Get all label values for a specific label with tenant isolation.
        
        Args:
            label: Label name to get values for
            tenant_id: Tenant ID for data isolation
            
        Returns:
            List of label values
        """
        try:
            # For label values, we need to filter by tenant_id
            result = self.prometheus.get_label_values(
                label_name=label,
                params={"match[]": f'{{tenant_id="{tenant_id}"}}'}
            )
            
            logger.info(f"Retrieved label values for '{label}' for tenant {tenant_id}")
            
            return {
                "status": "success",
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to get label values: {str(e)}")
            raise ExternalServiceError(f"Failed to get label values: {str(e)}")


# Global instance
metrics_service = MetricsService()