"""
Metrics service for querying Prometheus/Thanos API with tenant isolation.
"""

import logging
import re
from typing import Dict, Any, Optional
from prometheus_api_client import PrometheusConnect
from fastapi import HTTPException, status

from app.core.config import settings

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
        
        Args:
            query: Original PromQL query
            tenant_id: Tenant ID to inject
            
        Returns:
            Modified query with tenant_id label injected
        """
        tenant_label = f'tenant_id="{tenant_id}"'
        
        # Find all metric names in the query. This is a best-effort approach
        # without a full PromQL parser. It looks for words that are not operators
        # or keywords and are followed by a '{' or a space.
        metric_names = re.findall(r'([a-zA-Z_:][a-zA-Z0-9_:]+)(?=\s*\{|\s*(?:$|,|\)|\s|\[))', query)
        
        # Keywords to ignore to avoid incorrectly injecting labels
        ignore_keywords = {'by', 'sum', 'rate', 'increase', 'delta', 'irate', 'avg', 'min', 'max', 'group', 'count'}
        
        modified_query = query
        for metric_name in set(metric_names):
            if metric_name in ignore_keywords:
                continue

            # Regex to find the metric name with optional labels
            pattern = re.compile(r'\b' + metric_name + r'\b(\{[^}]*\})?')
            
            def replace(match):
                existing_labels = match.group(1)
                if existing_labels:
                    return f"{metric_name}{{{existing_labels[1:-1]},{tenant_label}}}"
                else:
                    return f"{metric_name}{{{tenant_label}}}"

            modified_query = pattern.sub(replace, modified_query)

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
            HTTPException: If query fails or returns invalid data
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query metrics: {str(e)}"
            )
    
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
            HTTPException: If query fails or returns invalid data
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query metrics range: {str(e)}"
            )
    
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get label values: {str(e)}"
            )


# Global instance
metrics_service = MetricsService()
