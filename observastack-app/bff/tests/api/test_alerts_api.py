"""Integration tests for alert API endpoints."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.models.alerts import AlertWebhookPayload
from app.auth.models import UserContext


class TestAlertsAPI:
    """Test cases for alerts API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.tenant_id = "test_tenant"
        
        # Mock authentication
        self.mock_user = UserContext(
            user_id="test_user",
            tenant_id=self.tenant_id,
            roles=["user"],
            expires_at=datetime.utcnow()
        )
    
    def create_sample_webhook_payload(self) -> dict:
        """Create a sample webhook payload for testing."""
        return {
            "version": "4",
            "groupKey": "test_group",
            "status": "firing",
            "receiver": "webhook",
            "groupLabels": {"alertname": "HighCPU"},
            "commonLabels": {"job": "node-exporter"},
            "commonAnnotations": {"description": "CPU usage is high"},
            "externalURL": "http://alertmanager:9093",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "HighCPU",
                        "instance": "server1:9100",
                        "job": "node-exporter",
                        "severity": "critical"
                    },
                    "annotations": {
                        "description": "CPU usage above 90%",
                        "summary": "High CPU usage detected"
                    },
                    "startsAt": "2025-08-16T07:48:27.000Z",
                    "endsAt": "",
                    "generatorURL": "http://prometheus:9090/graph?g0.expr=cpu_usage%3E90"
                }
            ]
        }
    
    def test_alertmanager_webhook_success(self):
        """Test successful Alertmanager webhook processing."""
        
        payload = self.create_sample_webhook_payload()
        
        response = self.client.post(
            "/api/v1/alerts/webhook/alertmanager",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["processed_count"] == 1
        assert data["group_key"] == "test_group"
    
    def test_generic_webhook_success(self):
        """Test successful generic webhook processing."""
        
        # Generic webhook payload (simplified)
        payload = {
            "alertname": "CustomAlert",
            "severity": "high",
            "message": "Custom alert triggered",
            "labels": {
                "service": "api",
                "environment": "production"
            }
        }
        
        response = self.client.post(
            "/api/v1/alerts/webhook/generic",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["processed_count"] == 1
        assert data["source"] == "generic"
    
    @patch('app.api.v1.alerts.get_current_user')
    @patch('app.api.v1.alerts.get_current_tenant')
    def test_get_alerts_success(self, mock_get_tenant, mock_get_user):
        """Test successful alert retrieval."""
        mock_get_tenant.return_value = self.tenant_id
        mock_get_user.return_value = self.mock_user
        
        response = self.client.get("/api/v1/alerts")
        
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        assert isinstance(data["alerts"], list)
        assert isinstance(data["total"], int)
    
    @patch('app.api.v1.alerts.get_current_user')
    @patch('app.api.v1.alerts.get_current_tenant')
    def test_get_alerts_with_filters(self, mock_get_tenant, mock_get_user):
        """Test alert retrieval with filters."""
        mock_get_tenant.return_value = self.tenant_id
        mock_get_user.return_value = self.mock_user
        
        response = self.client.get(
            "/api/v1/alerts",
            params={
                "severity": ["critical", "high"],
                "status": ["active"],
                "limit": 10,
                "offset": 0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data
    
    @patch('app.api.v1.alerts.get_current_user')
    @patch('app.api.v1.alerts.get_current_tenant')
    def test_get_alert_statistics(self, mock_get_tenant, mock_get_user):
        """Test alert statistics retrieval."""
        mock_get_tenant.return_value = self.tenant_id
        mock_get_user.return_value = self.mock_user
        
        response = self.client.get("/api/v1/alerts/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_severity" in data
        assert "by_source" in data
    
    @patch('app.api.v1.alerts.get_current_user')
    @patch('app.api.v1.alerts.get_current_tenant')
    def test_alert_service_health(self, mock_get_tenant, mock_get_user):
        """Test alert service health check."""
        response = self.client.get("/api/v1/alerts/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "timestamp" in data
    
    def test_webhook_invalid_payload(self):
        """Test webhook with invalid payload."""
        invalid_payload = {"invalid": "data"}
        
        response = self.client.post(
            "/api/v1/alerts/webhook/alertmanager",
            json=invalid_payload
        )
        
        # Should return 422 for validation error or 500 for processing error
        assert response.status_code in [422, 500]
    
    @patch('app.api.v1.alerts.get_current_user')
    @patch('app.api.v1.alerts.get_current_tenant')
    def test_perform_alert_action_invalid_request(self, mock_get_tenant, mock_get_user):
        """Test alert action with invalid request."""
        mock_get_tenant.return_value = self.tenant_id
        mock_get_user.return_value = self.mock_user
        
        # Invalid action request (missing required fields)
        invalid_request = {
            "alert_ids": [],  # Empty list
            "action": "invalid_action"
        }
        
        response = self.client.post(
            "/api/v1/alerts/actions",
            json=invalid_request
        )
        
        assert response.status_code == 400  # Bad request
    
    @patch('app.api.v1.alerts.get_current_user')
    @patch('app.api.v1.alerts.get_current_tenant')
    def test_create_silence_invalid_request(self, mock_get_tenant, mock_get_user):
        """Test silence creation with invalid request."""
        mock_get_tenant.return_value = self.tenant_id
        mock_get_user.return_value = self.mock_user
        
        # Invalid silence request (missing required fields)
        invalid_request = {
            "matchers": [],  # Empty matchers
            "comment": "Test silence"
        }
        
        response = self.client.post(
            "/api/v1/alerts/silences",
            json=invalid_request
        )
        
        assert response.status_code == 422  # Validation error