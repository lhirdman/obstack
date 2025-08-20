"""Unit tests for AlertService."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json

from app.services.alert_service import AlertService, AlertDeduplicator, AlertGrouper
from app.models.alerts import (
    Alert, AlertWebhookPayload, AlertActionRequest, AlertQuery, 
    AlertStatus, AlertSource, SeverityLevel, SilenceRequest
)
from app.exceptions import AlertException, ValidationError


class TestAlertDeduplicator:
    """Test cases for AlertDeduplicator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.deduplicator = AlertDeduplicator()
    
    def test_generate_fingerprint_consistent(self):
        """Test that fingerprint generation is consistent."""
        alert_data = {
            'labels': {
                'alertname': 'HighCPU',
                'instance': 'server1:9100',
                'job': 'node-exporter',
                'severity': 'critical'
            }
        }
        
        fingerprint1 = self.deduplicator.generate_fingerprint(alert_data)
        fingerprint2 = self.deduplicator.generate_fingerprint(alert_data)
        
        assert fingerprint1 == fingerprint2
        assert len(fingerprint1) == 16  # SHA256 truncated to 16 chars
    
    def test_generate_fingerprint_different_for_different_alerts(self):
        """Test that different alerts generate different fingerprints."""
        alert_data1 = {
            'labels': {
                'alertname': 'HighCPU',
                'instance': 'server1:9100',
                'job': 'node-exporter',
                'severity': 'critical'
            }
        }
        
        alert_data2 = {
            'labels': {
                'alertname': 'HighMemory',
                'instance': 'server1:9100',
                'job': 'node-exporter',
                'severity': 'critical'
            }
        }
        
        fingerprint1 = self.deduplicator.generate_fingerprint(alert_data1)
        fingerprint2 = self.deduplicator.generate_fingerprint(alert_data2)
        
        assert fingerprint1 != fingerprint2
    
    def test_duplicate_detection(self):
        """Test duplicate alert detection."""
        fingerprint = "test_fingerprint"
        alert_id = "alert_123"
        group_key = "group_123"
        
        # Initially not a duplicate
        assert not self.deduplicator.is_duplicate(fingerprint)
        
        # Register alert
        self.deduplicator.register_alert(fingerprint, alert_id, group_key)
        
        # Now it's a duplicate
        assert self.deduplicator.is_duplicate(fingerprint)
        assert self.deduplicator.get_existing_alert_id(fingerprint) == alert_id
    
    def test_remove_alert(self):
        """Test alert removal from deduplication tracking."""
        fingerprint = "test_fingerprint"
        alert_id = "alert_123"
        group_key = "group_123"
        
        # Register and then remove
        self.deduplicator.register_alert(fingerprint, alert_id, group_key)
        assert self.deduplicator.is_duplicate(fingerprint)
        
        self.deduplicator.remove_alert(fingerprint, alert_id, group_key)
        assert not self.deduplicator.is_duplicate(fingerprint)


class TestAlertGrouper:
    """Test cases for AlertGrouper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.grouper = AlertGrouper()
    
    def test_generate_group_key_consistent(self):
        """Test that group key generation is consistent."""
        alert_data = {
            'labels': {
                'alertname': 'HighCPU',
                'job': 'node-exporter',
                'cluster': 'prod'
            }
        }
        
        key1 = self.grouper.generate_group_key(alert_data)
        key2 = self.grouper.generate_group_key(alert_data)
        
        assert key1 == key2
        assert len(key1) == 12  # SHA256 truncated to 12 chars
    
    def test_get_or_create_group(self):
        """Test group creation and retrieval."""
        group_key = "test_group"
        common_labels = {"alertname": "HighCPU", "job": "node-exporter"}
        
        # Create new group
        group1 = self.grouper.get_or_create_group(group_key, common_labels)
        assert group1.group_key == group_key
        assert group1.common_labels == common_labels
        assert group1.status == AlertStatus.ACTIVE
        
        # Get existing group
        group2 = self.grouper.get_or_create_group(group_key, common_labels)
        assert group1.id == group2.id
    
    def test_add_alert_to_group(self):
        """Test adding alerts to groups."""
        group_key = "test_group"
        common_labels = {"alertname": "HighCPU"}
        
        # Create group and alert
        group = self.grouper.get_or_create_group(group_key, common_labels)
        alert = Alert(
            id="alert_123",
            severity=SeverityLevel.HIGH,
            title="High CPU Usage",
            description="CPU usage is high",
            source=AlertSource.PROMETHEUS,
            timestamp=datetime.utcnow(),
            tenant_id="tenant_123",
            fingerprint="fingerprint_123",
            starts_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add alert to group
        initial_count = len(group.alerts)
        self.grouper.add_alert_to_group(group_key, alert)
        
        updated_group = self.grouper._groups[group_key]
        assert len(updated_group.alerts) == initial_count + 1
        assert alert in updated_group.alerts


class TestAlertService:
    """Test cases for AlertService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = AlertService()
        self.tenant_id = "test_tenant"
        self.user_id = "test_user"
    
    def create_sample_webhook_payload(self) -> AlertWebhookPayload:
        """Create a sample webhook payload for testing."""
        return AlertWebhookPayload(
            version="4",
            group_key="test_group",
            status="firing",
            receiver="webhook",
            group_labels={"alertname": "HighCPU"},
            common_labels={"job": "node-exporter"},
            common_annotations={"description": "CPU usage is high"},
            external_url="http://alertmanager:9093",
            alerts=[
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
        )
    
    @pytest.mark.asyncio
    async def test_process_webhook_new_alert(self):
        """Test processing webhook with new alert."""
        payload = self.create_sample_webhook_payload()
        
        processed_alerts = await self.service.process_webhook(payload, self.tenant_id)
        
        assert len(processed_alerts) == 1
        alert = processed_alerts[0]
        
        assert alert.title == "HighCPU"
        assert alert.severity == SeverityLevel.CRITICAL
        assert alert.source == AlertSource.PROMETHEUS
        assert alert.status == AlertStatus.ACTIVE
        assert alert.tenant_id == self.tenant_id
        assert "alertname" in alert.labels
        assert "description" in alert.annotations
    
    @pytest.mark.asyncio
    async def test_process_webhook_duplicate_alert(self):
        """Test processing webhook with duplicate alert."""
        payload = self.create_sample_webhook_payload()
        
        # Process first time
        alerts1 = await self.service.process_webhook(payload, self.tenant_id)
        assert len(alerts1) == 1
        original_alert_id = alerts1[0].id
        
        # Process same alert again
        alerts2 = await self.service.process_webhook(payload, self.tenant_id)
        assert len(alerts2) == 1
        assert alerts2[0].id == original_alert_id  # Same alert updated
    
    @pytest.mark.asyncio
    async def test_process_webhook_resolved_alert(self):
        """Test processing webhook with resolved alert."""
        payload = self.create_sample_webhook_payload()
        
        # First, create active alert
        await self.service.process_webhook(payload, self.tenant_id)
        
        # Now send resolved version
        payload.status = "resolved"
        payload.alerts[0]["status"] = "resolved"
        payload.alerts[0]["endsAt"] = "2025-08-16T08:48:27.000Z"
        
        processed_alerts = await self.service.process_webhook(payload, self.tenant_id)
        
        assert len(processed_alerts) == 1
        alert = processed_alerts[0]
        assert alert.status == AlertStatus.RESOLVED
        assert alert.ends_at is not None
    
    def test_parse_severity(self):
        """Test severity parsing."""
        assert self.service._parse_severity("critical") == SeverityLevel.CRITICAL
        assert self.service._parse_severity("high") == SeverityLevel.HIGH
        assert self.service._parse_severity("warning") == SeverityLevel.MEDIUM
        assert self.service._parse_severity("medium") == SeverityLevel.MEDIUM
        assert self.service._parse_severity("low") == SeverityLevel.LOW
        assert self.service._parse_severity("info") == SeverityLevel.INFO
        assert self.service._parse_severity("unknown") == SeverityLevel.MEDIUM  # default
    
    def test_determine_source(self):
        """Test alert source determination."""
        # Prometheus source
        labels = {"job": "node-exporter"}
        assert self.service._determine_source(labels, "prometheus") == AlertSource.PROMETHEUS
        
        # Loki source
        labels = {"alertname": "LogErrorRate"}
        assert self.service._determine_source(labels, "loki") == AlertSource.LOKI
        
        # Tempo source
        labels = {"alertname": "TraceLatency"}
        assert self.service._determine_source(labels, "tempo") == AlertSource.TEMPO
        
        # OpenSearch source
        labels = {}
        assert self.service._determine_source(labels, "opensearch") == AlertSource.OPENSEARCH
        
        # External source (default)
        labels = {}
        assert self.service._determine_source(labels, "custom") == AlertSource.EXTERNAL
    
    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        # Valid RFC3339 timestamp
        timestamp_str = "2025-08-16T07:48:27.000Z"
        parsed = self.service._parse_timestamp(timestamp_str)
        assert parsed is not None
        assert isinstance(parsed, datetime)
        
        # Invalid timestamp
        invalid_timestamp = "invalid-timestamp"
        parsed = self.service._parse_timestamp(invalid_timestamp)
        assert parsed is None
        
        # None timestamp
        parsed = self.service._parse_timestamp(None)
        assert parsed is None
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self):
        """Test alert acknowledgment."""
        # Create an alert first
        payload = self.create_sample_webhook_payload()
        processed_alerts = await self.service.process_webhook(payload, self.tenant_id)
        alert = processed_alerts[0]
        
        # Acknowledge the alert
        request = AlertActionRequest(
            alert_ids=[alert.id],
            action="acknowledge"
        )
        
        response = await self.service.perform_action(request, self.user_id, self.tenant_id)
        
        assert response.success
        assert response.affected_alerts == 1
        assert len(response.failed_alerts) == 0
        
        # Verify alert status changed
        updated_alert = self.service._alerts[alert.id]
        assert updated_alert.status == AlertStatus.ACKNOWLEDGED
        assert updated_alert.assignee == self.user_id
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self):
        """Test alert resolution."""
        # Create an alert first
        payload = self.create_sample_webhook_payload()
        processed_alerts = await self.service.process_webhook(payload, self.tenant_id)
        alert = processed_alerts[0]
        
        # Resolve the alert
        request = AlertActionRequest(
            alert_ids=[alert.id],
            action="resolve"
        )
        
        response = await self.service.perform_action(request, self.user_id, self.tenant_id)
        
        assert response.success
        assert response.affected_alerts == 1
        
        # Verify alert status changed
        updated_alert = self.service._alerts[alert.id]
        assert updated_alert.status == AlertStatus.RESOLVED
        assert updated_alert.ends_at is not None
    
    @pytest.mark.asyncio
    async def test_assign_alert(self):
        """Test alert assignment."""
        # Create an alert first
        payload = self.create_sample_webhook_payload()
        processed_alerts = await self.service.process_webhook(payload, self.tenant_id)
        alert = processed_alerts[0]
        
        # Assign the alert
        assignee = "another_user"
        request = AlertActionRequest(
            alert_ids=[alert.id],
            action="assign",
            assignee=assignee
        )
        
        response = await self.service.perform_action(request, self.user_id, self.tenant_id)
        
        assert response.success
        assert response.affected_alerts == 1
        
        # Verify alert assignment
        updated_alert = self.service._alerts[alert.id]
        assert updated_alert.assignee == assignee
    
    @pytest.mark.asyncio
    async def test_silence_alert(self):
        """Test alert silencing."""
        # Create an alert first
        payload = self.create_sample_webhook_payload()
        processed_alerts = await self.service.process_webhook(payload, self.tenant_id)
        alert = processed_alerts[0]
        
        # Silence the alert
        request = AlertActionRequest(
            alert_ids=[alert.id],
            action="silence",
            silence_duration="1h"
        )
        
        response = await self.service.perform_action(request, self.user_id, self.tenant_id)
        
        assert response.success
        assert response.affected_alerts == 1
        
        # Verify alert silencing
        updated_alert = self.service._alerts[alert.id]
        assert updated_alert.status == AlertStatus.SILENCED
        assert updated_alert.silence_id is not None
        
        # Verify silence was created
        silence = self.service._silences[updated_alert.silence_id]
        assert silence.created_by == self.user_id
        assert silence.status == "active"
    
    @pytest.mark.asyncio
    async def test_perform_action_invalid_alert_id(self):
        """Test performing action on non-existent alert."""
        request = AlertActionRequest(
            alert_ids=["non_existent_alert"],
            action="acknowledge"
        )
        
        response = await self.service.perform_action(request, self.user_id, self.tenant_id)
        
        assert response.success  # Action completes but with failures
        assert response.affected_alerts == 0
        assert "non_existent_alert" in response.failed_alerts
    
    @pytest.mark.asyncio
    async def test_perform_action_wrong_tenant(self):
        """Test performing action on alert from different tenant."""
        # Create alert for different tenant
        payload = self.create_sample_webhook_payload()
        processed_alerts = await self.service.process_webhook(payload, "other_tenant")
        alert = processed_alerts[0]
        
        # Try to act on it with different tenant
        request = AlertActionRequest(
            alert_ids=[alert.id],
            action="acknowledge"
        )
        
        response = await self.service.perform_action(request, self.user_id, self.tenant_id)
        
        assert response.success  # Action completes but with failures
        assert response.affected_alerts == 0
        assert alert.id in response.failed_alerts
    
    @pytest.mark.asyncio
    async def test_get_alerts_filtering(self):
        """Test alert retrieval with filtering."""
        # Create multiple alerts with different properties
        payload1 = self.create_sample_webhook_payload()
        payload1.alerts[0]["labels"]["severity"] = "critical"
        await self.service.process_webhook(payload1, self.tenant_id)
        
        payload2 = self.create_sample_webhook_payload()
        payload2.alerts[0]["labels"]["alertname"] = "HighMemory"
        payload2.alerts[0]["labels"]["severity"] = "warning"
        await self.service.process_webhook(payload2, self.tenant_id)
        
        # Test filtering by severity
        query = AlertQuery(severity=[SeverityLevel.CRITICAL])
        response = await self.service.get_alerts(query, self.tenant_id)
        
        assert response.success
        assert response.total == 1
        assert response.alerts[0].severity == SeverityLevel.CRITICAL
        
        # Test filtering by status
        query = AlertQuery(status=[AlertStatus.ACTIVE])
        response = await self.service.get_alerts(query, self.tenant_id)
        
        assert response.success
        assert response.total == 2  # Both alerts are active
    
    @pytest.mark.asyncio
    async def test_get_alerts_pagination(self):
        """Test alert retrieval with pagination."""
        # Create multiple alerts
        for i in range(5):
            payload = self.create_sample_webhook_payload()
            payload.alerts[0]["labels"]["instance"] = f"server{i}:9100"
            await self.service.process_webhook(payload, self.tenant_id)
        
        # Test pagination
        query = AlertQuery(limit=2, offset=0)
        response = await self.service.get_alerts(query, self.tenant_id)
        
        assert response.success
        assert len(response.alerts) == 2
        assert response.total == 5
        
        # Test second page
        query = AlertQuery(limit=2, offset=2)
        response = await self.service.get_alerts(query, self.tenant_id)
        
        assert response.success
        assert len(response.alerts) == 2
        assert response.total == 5
    
    @pytest.mark.asyncio
    async def test_get_alert_statistics(self):
        """Test alert statistics calculation."""
        # Create alerts with different statuses and severities
        payload1 = self.create_sample_webhook_payload()
        payload1.alerts[0]["labels"]["severity"] = "critical"
        alerts1 = await self.service.process_webhook(payload1, self.tenant_id)
        
        payload2 = self.create_sample_webhook_payload()
        payload2.alerts[0]["labels"]["alertname"] = "HighMemory"
        payload2.alerts[0]["labels"]["severity"] = "warning"
        alerts2 = await self.service.process_webhook(payload2, self.tenant_id)
        
        # Acknowledge one alert
        await self.service._acknowledge_alert(alerts1[0], self.user_id)
        
        # Get statistics
        stats = await self.service.get_alert_statistics(self.tenant_id)
        
        assert stats.total == 2
        assert stats.by_status[AlertStatus.ACKNOWLEDGED] == 1
        assert stats.by_status[AlertStatus.ACTIVE] == 1
        assert stats.by_severity[SeverityLevel.CRITICAL] == 1
        assert stats.by_severity[SeverityLevel.MEDIUM] == 1  # warning maps to medium
    
    @pytest.mark.asyncio
    async def test_create_silence(self):
        """Test silence creation."""
        silence_request = SilenceRequest(
            matchers=[{"name": "alertname", "value": "HighCPU", "isRegex": "false"}],
            starts_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(hours=1),
            created_by=self.user_id,
            comment="Maintenance window"
        )
        
        silence = await self.service.create_silence(silence_request, self.user_id, self.tenant_id)
        
        assert silence.id is not None
        assert silence.created_by == self.user_id
        assert silence.comment == "Maintenance window"
        assert silence.status == "active"
        assert len(silence.matchers) == 1
    
    def test_parse_duration(self):
        """Test duration parsing."""
        # Test valid durations
        future_time = self.service._parse_duration("30m")
        assert future_time > datetime.utcnow()
        
        future_time = self.service._parse_duration("2h")
        assert future_time > datetime.utcnow()
        
        future_time = self.service._parse_duration("1d")
        assert future_time > datetime.utcnow()
        
        # Test invalid duration
        with pytest.raises(ValidationError):
            self.service._parse_duration("invalid")
        
        with pytest.raises(ValidationError):
            self.service._parse_duration("30x")  # Invalid unit
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health check."""
        health = await self.service.health_check()
        
        assert isinstance(health, dict)
        assert "alert_service" in health
        assert "deduplication" in health
        assert "grouping" in health
        assert "storage" in health
        assert all(isinstance(v, bool) for v in health.values())
    
    @pytest.mark.asyncio
    async def test_process_webhook_exception_handling(self):
        """Test webhook processing with invalid data."""
        # Test with invalid payload structure
        invalid_payload = AlertWebhookPayload(
            version="4",
            group_key="test",
            status="firing",
            receiver="test",
            external_url="http://test",
            alerts=[]  # Empty alerts list
        )
        
        # Should not raise exception, just return empty list
        processed_alerts = await self.service.process_webhook(invalid_payload, self.tenant_id)
        assert len(processed_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_tenant_isolation(self):
        """Test that tenant isolation works correctly."""
        tenant1 = "tenant_1"
        tenant2 = "tenant_2"
        
        # Create alerts for different tenants
        payload1 = self.create_sample_webhook_payload()
        payload1.alerts[0]["labels"]["instance"] = "server1:9100"
        await self.service.process_webhook(payload1, tenant1)
        
        payload2 = self.create_sample_webhook_payload()
        payload2.alerts[0]["labels"]["instance"] = "server2:9100"
        await self.service.process_webhook(payload2, tenant2)
        
        # Verify tenant1 only sees their alerts
        query = AlertQuery()
        response1 = await self.service.get_alerts(query, tenant1)
        assert response1.total == 1
        assert response1.alerts[0].tenant_id == tenant1
        
        # Verify tenant2 only sees their alerts
        response2 = await self.service.get_alerts(query, tenant2)
        assert response2.total == 1
        assert response2.alerts[0].tenant_id == tenant2
        
        # Verify statistics are tenant-isolated
        stats1 = await self.service.get_alert_statistics(tenant1)
        stats2 = await self.service.get_alert_statistics(tenant2)
        
        assert stats1.total == 1
        assert stats2.total == 1