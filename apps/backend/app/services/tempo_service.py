"""
Tempo service for querying distributed traces with tenant isolation.
"""

import logging
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings
from app.core.error_handling import ExternalServiceError

logger = logging.getLogger(__name__)


class TempoService:
    """Service for querying Tempo with tenant isolation."""
    
    def __init__(self):
        """Initialize the Tempo HTTP client."""
        self.base_url = settings.tempo_url.rstrip('/')
        self.timeout = settings.tempo_timeout
        logger.info(f"Initialized Tempo client with URL: {self.base_url}")
    
    def _validate_tenant_access(self, trace_data: Dict[str, Any], tenant_id: int) -> bool:
        """
        Validate that the trace belongs to the specified tenant.
        
        This checks for tenant_id in the trace tags/attributes to ensure
        proper tenant isolation.
        
        Args:
            trace_data: Trace data from Tempo API
            tenant_id: Tenant ID to validate against
            
        Returns:
            bool: True if trace belongs to tenant, False otherwise
        """
        if not trace_data or not isinstance(trace_data, dict):
            return False
        
        # Check if trace has batches with resource spans
        batches = trace_data.get('batches', [])
        if not batches:
            return False
        
        # Look for tenant_id in resource attributes or span attributes
        for batch in batches:
            resource = batch.get('resource', {})
            attributes = resource.get('attributes', [])
            
            # Check resource attributes for tenant_id
            for attr in attributes:
                if (attr.get('key') == 'tenant_id' and 
                    str(attr.get('value', {}).get('stringValue', '')) == str(tenant_id)):
                    return True
            
            # Check span attributes for tenant_id
            scopes = batch.get('scopeSpans', [])
            for scope in scopes:
                spans = scope.get('spans', [])
                for span in spans:
                    span_attributes = span.get('attributes', [])
                    for attr in span_attributes:
                        if (attr.get('key') == 'tenant_id' and 
                            str(attr.get('value', {}).get('stringValue', '')) == str(tenant_id)):
                            return True
        
        return False
    
    async def get_trace(self, trace_id: str, tenant_id: int) -> Dict[str, Any]:
        """
        Retrieve a specific trace by ID with tenant isolation.
        
        Args:
            trace_id: Trace ID to retrieve
            tenant_id: Tenant ID for access validation
            
        Returns:
            Trace data from Tempo
            
        Raises:
            ExternalServiceError: If trace retrieval fails
            HTTPException: If trace doesn't belong to tenant (404)
        """
        try:
            # Validate trace_id format (should be hex string)
            if not trace_id or not all(c in '0123456789abcdefABCDEF' for c in trace_id):
                raise ExternalServiceError("Invalid trace ID format")
            
            # Query Tempo API for the trace
            url = f"{self.base_url}/api/traces/{trace_id}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    raise ExternalServiceError("Trace not found", status_code=404)
                elif response.status_code != 200:
                    raise ExternalServiceError(
                        f"Tempo API returned status {response.status_code}: {response.text}",
                        status_code=response.status_code
                    )
                
                trace_data = response.json()
                
                # Validate tenant access to this trace
                if not self._validate_tenant_access(trace_data, tenant_id):
                    logger.warning(f"Tenant {tenant_id} attempted to access trace {trace_id} without permission")
                    raise ExternalServiceError("Trace not found", status_code=404)
                
                logger.info(f"Retrieved trace {trace_id} for tenant {tenant_id}")
                return trace_data
                
        except ExternalServiceError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve trace {trace_id}: {str(e)}")
            raise ExternalServiceError(f"Failed to retrieve trace: {str(e)}")
    
    async def search_traces(
        self, 
        tenant_id: int,
        service: Optional[str] = None,
        operation: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for traces with tenant isolation.
        
        Args:
            tenant_id: Tenant ID for filtering
            service: Optional service name filter
            operation: Optional operation name filter
            start: Optional start time (Unix timestamp in seconds)
            end: Optional end time (Unix timestamp in seconds)
            limit: Optional limit on number of results
            
        Returns:
            Search results from Tempo
        """
        try:
            url = f"{self.base_url}/api/search"
            
            # Build query parameters with tenant isolation
            params = {
                'tags': f'tenant_id={tenant_id}'
            }
            
            if service:
                params['service'] = service
            if operation:
                params['operation'] = operation
            if start:
                params['start'] = start
            if end:
                params['end'] = end
            if limit:
                params['limit'] = limit
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Tempo search API returned status {response.status_code}: {response.text}",
                        status_code=response.status_code
                    )
                
                search_results = response.json()
                logger.info(f"Search completed for tenant {tenant_id}")
                return search_results
                
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to search traces for tenant {tenant_id}: {str(e)}")
            raise ExternalServiceError(f"Failed to search traces: {str(e)}")


# Global instance
tempo_service = TempoService()