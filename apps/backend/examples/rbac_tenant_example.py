"""
Example demonstrating RBAC and tenant isolation functionality.

This example shows how to use the new multi-tenant context and RBAC
features implemented in task 2.2.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from app.auth.models import UserContext
from app.auth.rbac import Permission, rbac_manager, require_permission
from app.auth.tenant_context import (
    tenant_context, 
    TenantIsolationMixin,
    create_tenant_aware_query,
    validate_tenant_data_access
)


class LogService(TenantIsolationMixin):
    """Example service demonstrating tenant isolation."""
    
    def __init__(self):
        """Initialize the log service."""
        # Mock data for demonstration
        self.logs = [
            {"id": 1, "tenant_id": "tenant-a", "level": "error", "message": "Database connection failed"},
            {"id": 2, "tenant_id": "tenant-b", "level": "info", "message": "User logged in"},
            {"id": 3, "tenant_id": "tenant-a", "level": "warning", "message": "High memory usage"},
            {"id": 4, "tenant_id": "tenant-c", "level": "error", "message": "API timeout"},
        ]
    
    @require_permission(Permission.LOGS_READ)
    def get_logs(self, user_context: UserContext, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get logs with tenant isolation and permission checking."""
        # Add tenant filters to ensure isolation
        query_filters = self.add_tenant_filters(filters or {})
        
        # Filter logs based on tenant
        tenant_logs = [
            log for log in self.logs 
            if log.get("tenant_id") == query_filters.get("tenant_id")
        ]
        
        # Apply additional filters
        if "level" in query_filters:
            tenant_logs = [
                log for log in tenant_logs 
                if log.get("level") == query_filters["level"]
            ]
        
        # Log the access for audit
        self.log_tenant_access("get_logs", f"returned {len(tenant_logs)} logs")
        
        return tenant_logs
    
    @require_permission(Permission.LOGS_WRITE)
    def create_log(self, user_context: UserContext, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new log entry with tenant isolation."""
        # Validate that the log data belongs to the current tenant
        validate_tenant_data_access(log_data)
        
        # Add tenant context to the log
        context = self.get_tenant_context()
        log_data["tenant_id"] = context.tenant_id
        log_data["id"] = len(self.logs) + 1
        
        # Add to mock storage
        self.logs.append(log_data)
        
        self.log_tenant_access("create_log", f"created log {log_data['id']}")
        
        return log_data


class AlertService(TenantIsolationMixin):
    """Example service for alert management with RBAC."""
    
    def __init__(self):
        """Initialize the alert service."""
        self.alerts = [
            {"id": 1, "tenant_id": "tenant-a", "severity": "critical", "title": "Database down"},
            {"id": 2, "tenant_id": "tenant-b", "severity": "warning", "title": "High CPU usage"},
            {"id": 3, "tenant_id": "tenant-a", "severity": "info", "title": "Deployment completed"},
        ]
    
    @require_permission(Permission.ALERTS_READ)
    def get_alerts(self, user_context: UserContext) -> List[Dict[str, Any]]:
        """Get alerts for the current tenant."""
        return self.filter_tenant_results(self.alerts)
    
    @require_permission(Permission.ALERTS_ACKNOWLEDGE)
    def acknowledge_alert(self, user_context: UserContext, alert_id: int) -> Dict[str, Any]:
        """Acknowledge an alert."""
        # Find the alert
        alert = next((a for a in self.alerts if a["id"] == alert_id), None)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        
        # Validate tenant access to this alert
        validate_tenant_data_access(alert)
        
        # Update alert status
        alert["status"] = "acknowledged"
        alert["acknowledged_by"] = user_context.user_id
        alert["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
        
        self.log_tenant_access("acknowledge_alert", f"alert {alert_id}")
        
        return alert


def demonstrate_rbac_and_tenant_isolation():
    """Demonstrate RBAC and tenant isolation features."""
    
    print("=== RBAC and Tenant Isolation Demo ===\n")
    
    # Create different types of users
    admin_user = UserContext(
        user_id="admin-001",
        tenant_id="tenant-a",
        roles=["admin"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    
    viewer_user = UserContext(
        user_id="viewer-001",
        tenant_id="tenant-a",
        roles=["viewer"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    
    editor_user = UserContext(
        user_id="editor-001",
        tenant_id="tenant-b",
        roles=["editor"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    
    # Initialize services
    log_service = LogService()
    alert_service = AlertService()
    
    print("1. Testing RBAC Permissions:")
    print("-" * 30)
    
    # Test admin permissions
    print(f"Admin has LOGS_READ: {rbac_manager.has_permission(admin_user, Permission.LOGS_READ)}")
    print(f"Admin has LOGS_WRITE: {rbac_manager.has_permission(admin_user, Permission.LOGS_WRITE)}")
    print(f"Admin has TENANT_MANAGE: {rbac_manager.has_permission(admin_user, Permission.TENANT_MANAGE)}")
    
    # Test viewer permissions
    print(f"Viewer has LOGS_READ: {rbac_manager.has_permission(viewer_user, Permission.LOGS_READ)}")
    print(f"Viewer has LOGS_WRITE: {rbac_manager.has_permission(viewer_user, Permission.LOGS_WRITE)}")
    print(f"Viewer has ALERTS_ACKNOWLEDGE: {rbac_manager.has_permission(viewer_user, Permission.ALERTS_ACKNOWLEDGE)}")
    
    # Test editor permissions
    print(f"Editor has ALERTS_READ: {rbac_manager.has_permission(editor_user, Permission.ALERTS_READ)}")
    print(f"Editor has ALERTS_ACKNOWLEDGE: {rbac_manager.has_permission(editor_user, Permission.ALERTS_ACKNOWLEDGE)}")
    print(f"Editor has TENANT_MANAGE: {rbac_manager.has_permission(editor_user, Permission.TENANT_MANAGE)}")
    
    print("\n2. Testing Tenant Isolation:")
    print("-" * 30)
    
    # Test tenant-a user accessing their data
    with tenant_context("tenant-a", viewer_user):
        logs = log_service.get_logs(viewer_user)
        print(f"Viewer in tenant-a sees {len(logs)} logs")
        for log in logs:
            print(f"  - {log['level']}: {log['message']}")
    
    # Test tenant-b user accessing their data
    with tenant_context("tenant-b", editor_user):
        logs = log_service.get_logs(editor_user)
        print(f"Editor in tenant-b sees {len(logs)} logs")
        for log in logs:
            print(f"  - {log['level']}: {log['message']}")
        
        # Test alert acknowledgment
        alerts = alert_service.get_alerts(editor_user)
        print(f"Editor in tenant-b sees {len(alerts)} alerts")
        if alerts:
            acknowledged = alert_service.acknowledge_alert(editor_user, alerts[0]["id"])
            print(f"  - Acknowledged alert: {acknowledged['title']}")
    
    print("\n3. Testing Cross-Tenant Access (Admin):")
    print("-" * 40)
    
    # Admin accessing different tenant
    with tenant_context("tenant-b", admin_user, allow_cross_tenant=True):
        logs = log_service.get_logs(admin_user)
        print(f"Admin accessing tenant-b sees {len(logs)} logs")
    
    print("\n4. Testing Query Builder:")
    print("-" * 25)
    
    with tenant_context("tenant-a", viewer_user):
        # Build a tenant-aware query
        query = create_tenant_aware_query({"level": "error"}).add_tenant_filter().build()
        print(f"Generated query: {query}")
        
        # Use the query to filter logs
        filtered_logs = [
            log for log in log_service.logs
            if log.get("tenant_id") == query.get("tenant_id") and 
               log.get("level") == query.get("level")
        ]
        print(f"Query returned {len(filtered_logs)} error logs for tenant-a")
    
    print("\n5. Testing Permission Validation:")
    print("-" * 35)
    
    try:
        with tenant_context("tenant-a", viewer_user):
            # This should fail because viewer doesn't have LOGS_WRITE permission
            log_service.create_log(viewer_user, {
                "level": "info",
                "message": "Test log from viewer",
                "tenant_id": "tenant-a"
            })
    except Exception as e:
        print(f"Expected error for viewer trying to write logs: {type(e).__name__}")
    
    try:
        with tenant_context("tenant-a", admin_user):
            # This should succeed because admin has LOGS_WRITE permission
            new_log = log_service.create_log(admin_user, {
                "level": "info",
                "message": "Test log from admin",
                "tenant_id": "tenant-a"
            })
            print(f"Admin successfully created log: {new_log['id']}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    demonstrate_rbac_and_tenant_isolation()