"""Alert management service for ObservaStack."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from ..models.alerts import (
    Alert, AlertGroup, AlertStatus, AlertSource, AlertWebhookPayload,
    AlertActionRequest, AlertActionResponse, AlertQuery, AlertsResponse,
    AlertStatistics, SeverityLevel, Silence, SilenceRequest
)
from ..exceptions import AlertException, ValidationError, NotFoundError


class AlertDeduplicator:
    """Handles alert deduplication logic."""
    
    def __init__(self):
        self._alert_fingerprints: Dict[str, str] = {}  # fingerprint -> alert_id
        self._alert_groups: Dict[str, List[str]] = defaultdict(list)  # group_key -> alert_ids
    
    def generate_fingerprint(self, alert_data: Dict) -> str:
        """
        Generate a unique fingerprint for alert deduplication.
        
        Args:
            alert_data: Raw alert data from webhook
            
        Returns:
            Unique fingerprint string for the alert
        """
        # Extract key fields for fingerprint generation
        key_fields = {
            'alertname': alert_data.get('labels', {}).get('alertname', ''),
            'instance': alert_data.get('labels', {}).get('instance', ''),
            'job': alert_data.get('labels', {}).get('job', ''),
            'severity': alert_data.get('labels', {}).get('severity', ''),
        }
        
        # Create deterministic fingerprint
        fingerprint_data = json.dumps(key_fields, sort_keys=True)
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def is_duplicate(self, fingerprint: str) -> bool:
        """Check if alert with this fingerprint already exists."""
        return fingerprint in self._alert_fingerprints
    
    def register_alert(self, fingerprint: str, alert_id: str, group_key: str):
        """Register a new alert for deduplication tracking."""
        self._alert_fingerprints[fingerprint] = alert_id
        self._alert_groups[group_key].append(alert_id)
    
    def get_existing_alert_id(self, fingerprint: str) -> Optional[str]:
        """Get existing alert ID for a fingerprint."""
        return self._alert_fingerprints.get(fingerprint)
    
    def remove_alert(self, fingerprint: str, alert_id: str, group_key: str):
        """Remove alert from deduplication tracking."""
        self._alert_fingerprints.pop(fingerprint, None)
        if group_key in self._alert_groups:
            try:
                self._alert_groups[group_key].remove(alert_id)
                if not self._alert_groups[group_key]:
                    del self._alert_groups[group_key]
            except ValueError:
                pass  # Alert not in group


class AlertGrouper:
    """Handles alert grouping logic."""
    
    def __init__(self):
        self._groups: Dict[str, AlertGroup] = {}
    
    def generate_group_key(self, alert_data: Dict) -> str:
        """
        Generate group key for alert grouping.
        
        Args:
            alert_data: Raw alert data from webhook
            
        Returns:
            Group key for grouping related alerts
        """
        # Group by alertname and critical labels
        group_fields = {
            'alertname': alert_data.get('labels', {}).get('alertname', ''),
            'job': alert_data.get('labels', {}).get('job', ''),
            'cluster': alert_data.get('labels', {}).get('cluster', ''),
        }
        
        group_data = json.dumps(group_fields, sort_keys=True)
        return hashlib.sha256(group_data.encode()).hexdigest()[:12]
    
    def get_or_create_group(self, group_key: str, common_labels: Dict[str, str]) -> AlertGroup:
        """Get existing group or create new one."""
        if group_key not in self._groups:
            self._groups[group_key] = AlertGroup(
                id=f"group_{group_key}",
                alerts=[],
                common_labels=common_labels,
                group_key=group_key,
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        return self._groups[group_key]
    
    def add_alert_to_group(self, group_key: str, alert: Alert):
        """Add alert to group."""
        if group_key in self._groups:
            group = self._groups[group_key]
            group.alerts.append(alert)
            group.updated_at = datetime.utcnow()
            
            # Update group status based on alert statuses
            self._update_group_status(group)
    
    def remove_alert_from_group(self, group_key: str, alert_id: str):
        """Remove alert from group."""
        if group_key in self._groups:
            group = self._groups[group_key]
            group.alerts = [a for a in group.alerts if a.id != alert_id]
            group.updated_at = datetime.utcnow()
            
            if not group.alerts:
                del self._groups[group_key]
            else:
                self._update_group_status(group)
    
    def _update_group_status(self, group: AlertGroup):
        """Update group status based on alert statuses."""
        if not group.alerts:
            return
        
        statuses = {alert.status for alert in group.alerts}
        
        if AlertStatus.ACTIVE in statuses:
            group.status = AlertStatus.ACTIVE
        elif all(status == AlertStatus.RESOLVED for status in statuses):
            group.status = AlertStatus.RESOLVED
        elif all(status == AlertStatus.ACKNOWLEDGED for status in statuses):
            group.status = AlertStatus.ACKNOWLEDGED
        else:
            group.status = AlertStatus.ACTIVE  # Mixed states default to active


class AlertService:
    """Main alert management service."""
    
    def __init__(self):
        self._alerts: Dict[str, Alert] = {}  # alert_id -> Alert
        self._tenant_alerts: Dict[str, Set[str]] = defaultdict(set)  # tenant_id -> alert_ids
        self._deduplicator = AlertDeduplicator()
        self._grouper = AlertGrouper()
        self._silences: Dict[str, Silence] = {}
    
    async def process_webhook(self, payload: AlertWebhookPayload, tenant_id: str) -> List[Alert]:
        """
        Process incoming webhook payload and create/update alerts.
        
        Args:
            payload: Webhook payload from Alertmanager or other sources
            tenant_id: Tenant ID for multi-tenant isolation
            
        Returns:
            List of processed alerts
            
        Raises:
            AlertException: If processing fails
        """
        try:
            processed_alerts = []
            
            for alert_data in payload.alerts:
                alert = await self._process_single_alert(alert_data, payload, tenant_id)
                if alert:
                    processed_alerts.append(alert)
            
            return processed_alerts
            
        except Exception as e:
            raise AlertException(f"Failed to process webhook: {str(e)}") from e
    
    async def _process_single_alert(
        self, 
        alert_data: Dict, 
        payload: AlertWebhookPayload, 
        tenant_id: str
    ) -> Optional[Alert]:
        """Process a single alert from webhook payload."""
        
        # Generate fingerprint for deduplication
        fingerprint = self._deduplicator.generate_fingerprint(alert_data)
        
        # Check if this is a duplicate
        existing_alert_id = self._deduplicator.get_existing_alert_id(fingerprint)
        
        if existing_alert_id and existing_alert_id in self._alerts:
            # Update existing alert
            return await self._update_existing_alert(existing_alert_id, alert_data)
        
        # Create new alert
        return await self._create_new_alert(alert_data, payload, tenant_id, fingerprint)
    
    async def _create_new_alert(
        self, 
        alert_data: Dict, 
        payload: AlertWebhookPayload, 
        tenant_id: str, 
        fingerprint: str
    ) -> Alert:
        """Create a new alert from webhook data."""
        
        alert_id = str(uuid.uuid4())
        
        # Parse alert data
        labels = alert_data.get('labels', {})
        annotations = alert_data.get('annotations', {})
        
        # Determine severity
        severity = self._parse_severity(labels.get('severity', 'medium'))
        
        # Determine source
        source = self._determine_source(labels, payload.receiver)
        
        # Parse timestamps
        starts_at = self._parse_timestamp(alert_data.get('startsAt'))
        ends_at = self._parse_timestamp(alert_data.get('endsAt'))
        
        # Create alert
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=labels.get('alertname', 'Unknown Alert'),
            description=annotations.get('description', annotations.get('summary', '')),
            source=source,
            timestamp=datetime.utcnow(),
            status=AlertStatus.RESOLVED if ends_at else AlertStatus.ACTIVE,
            tenant_id=tenant_id,
            labels=labels,
            annotations=annotations,
            fingerprint=fingerprint,
            generator_url=alert_data.get('generatorURL'),
            starts_at=starts_at,
            ends_at=ends_at,
            updated_at=datetime.utcnow()
        )
        
        # Store alert
        self._alerts[alert_id] = alert
        self._tenant_alerts[tenant_id].add(alert_id)
        
        # Register for deduplication
        group_key = self._grouper.generate_group_key(alert_data)
        self._deduplicator.register_alert(fingerprint, alert_id, group_key)
        
        # Add to group
        group = self._grouper.get_or_create_group(group_key, payload.common_labels)
        self._grouper.add_alert_to_group(group_key, alert)
        
        return alert
    
    async def _update_existing_alert(self, alert_id: str, alert_data: Dict) -> Alert:
        """Update an existing alert with new data."""
        
        alert = self._alerts[alert_id]
        
        # Update timestamps and status
        ends_at = self._parse_timestamp(alert_data.get('endsAt'))
        
        if ends_at and alert.status == AlertStatus.ACTIVE:
            alert.status = AlertStatus.RESOLVED
            alert.ends_at = ends_at
        elif not ends_at and alert.status == AlertStatus.RESOLVED:
            alert.status = AlertStatus.ACTIVE
            alert.ends_at = None
        
        alert.updated_at = datetime.utcnow()
        
        # Update annotations (may contain new information)
        alert.annotations.update(alert_data.get('annotations', {}))
        
        return alert
    
    def _parse_severity(self, severity_str: str) -> SeverityLevel:
        """Parse severity string to SeverityLevel enum."""
        severity_map = {
            'critical': SeverityLevel.CRITICAL,
            'high': SeverityLevel.HIGH,
            'warning': SeverityLevel.MEDIUM,
            'medium': SeverityLevel.MEDIUM,
            'low': SeverityLevel.LOW,
            'info': SeverityLevel.INFO
        }
        return severity_map.get(severity_str.lower(), SeverityLevel.MEDIUM)
    
    def _determine_source(self, labels: Dict[str, str], receiver: str) -> AlertSource:
        """Determine alert source from labels and receiver."""
        
        # Check for specific source indicators in labels
        if 'prometheus' in receiver.lower() or labels.get('job'):
            return AlertSource.PROMETHEUS
        elif 'loki' in receiver.lower() or 'log' in labels.get('alertname', '').lower():
            return AlertSource.LOKI
        elif 'tempo' in receiver.lower() or 'trace' in labels.get('alertname', '').lower():
            return AlertSource.TEMPO
        elif 'opensearch' in receiver.lower() or 'elasticsearch' in receiver.lower():
            return AlertSource.OPENSEARCH
        else:
            return AlertSource.EXTERNAL
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return None
        
        try:
            # Handle RFC3339 format
            if timestamp_str.endswith('Z'):
                return datetime.fromisoformat(timestamp_str[:-1])
            else:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    async def perform_action(
        self, 
        request: AlertActionRequest, 
        user_id: str, 
        tenant_id: str
    ) -> AlertActionResponse:
        """
        Perform action on alerts (acknowledge, resolve, assign, silence).
        
        Args:
            request: Action request with alert IDs and action type
            user_id: User performing the action
            tenant_id: Tenant ID for authorization
            
        Returns:
            Action response with results
            
        Raises:
            AlertException: If action fails
            ValidationError: If request is invalid
        """
        
        if not request.alert_ids:
            raise ValidationError("No alert IDs provided")
        
        affected_count = 0
        failed_alerts = []
        
        for alert_id in request.alert_ids:
            try:
                # Verify alert exists and belongs to tenant
                if alert_id not in self._alerts:
                    failed_alerts.append(alert_id)
                    continue
                
                alert = self._alerts[alert_id]
                if alert.tenant_id != tenant_id:
                    failed_alerts.append(alert_id)
                    continue
                
                # Perform the requested action
                if request.action == "acknowledge":
                    await self._acknowledge_alert(alert, user_id)
                elif request.action == "resolve":
                    await self._resolve_alert(alert, user_id)
                elif request.action == "assign":
                    await self._assign_alert(alert, request.assignee, user_id)
                elif request.action == "silence":
                    await self._silence_alert(alert, request.silence_duration, user_id)
                
                affected_count += 1
                
            except Exception as e:
                failed_alerts.append(alert_id)
        
        return AlertActionResponse(
            success=True,
            message=f"Action '{request.action}' performed on {affected_count} alerts",
            affected_alerts=affected_count,
            failed_alerts=failed_alerts
        )
    
    async def _acknowledge_alert(self, alert: Alert, user_id: str):
        """Acknowledge an alert."""
        if alert.status == AlertStatus.ACTIVE:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.assignee = user_id
            alert.updated_at = datetime.utcnow()
    
    async def _resolve_alert(self, alert: Alert, user_id: str):
        """Resolve an alert."""
        alert.status = AlertStatus.RESOLVED
        alert.ends_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
    
    async def _assign_alert(self, alert: Alert, assignee: Optional[str], user_id: str):
        """Assign an alert to a user."""
        if not assignee:
            raise ValidationError("Assignee is required for assign action")
        
        alert.assignee = assignee
        alert.updated_at = datetime.utcnow()
    
    async def _silence_alert(self, alert: Alert, duration: Optional[str], user_id: str):
        """Silence an alert for a specified duration."""
        if not duration:
            raise ValidationError("Silence duration is required")
        
        # Parse duration (e.g., "1h", "30m", "2d")
        silence_until = self._parse_duration(duration)
        
        # Create silence
        silence_id = str(uuid.uuid4())
        silence = Silence(
            id=silence_id,
            matchers=[{"name": "fingerprint", "value": alert.fingerprint, "isRegex": "false"}],
            starts_at=datetime.utcnow(),
            ends_at=silence_until,
            created_by=user_id,
            comment=f"Silenced via alert action",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self._silences[silence_id] = silence
        alert.silence_id = silence_id
        alert.status = AlertStatus.SILENCED
        alert.updated_at = datetime.utcnow()
    
    def _parse_duration(self, duration_str: str) -> datetime:
        """Parse duration string to future datetime."""
        import re
        
        match = re.match(r'^(\d+)([smhd])$', duration_str)
        if not match:
            raise ValidationError(f"Invalid duration format: {duration_str}")
        
        value, unit = match.groups()
        value = int(value)
        
        if unit == 's':
            delta = timedelta(seconds=value)
        elif unit == 'm':
            delta = timedelta(minutes=value)
        elif unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        else:
            raise ValidationError(f"Invalid duration unit: {unit}")
        
        return datetime.utcnow() + delta
    
    async def get_alerts(self, query: AlertQuery, tenant_id: str) -> AlertsResponse:
        """
        Get alerts based on query parameters.
        
        Args:
            query: Query parameters for filtering alerts
            tenant_id: Tenant ID for data isolation
            
        Returns:
            Filtered alerts response
        """
        
        # Get tenant alerts
        tenant_alert_ids = self._tenant_alerts.get(tenant_id, set())
        alerts = [self._alerts[aid] for aid in tenant_alert_ids if aid in self._alerts]
        
        # Apply filters
        filtered_alerts = self._apply_filters(alerts, query)
        
        # Apply sorting
        sorted_alerts = self._apply_sorting(filtered_alerts, query.sort_by, query.sort_order)
        
        # Apply pagination
        total = len(sorted_alerts)
        paginated_alerts = sorted_alerts[query.offset:query.offset + query.limit]
        
        return AlertsResponse(
            success=True,
            message=f"Retrieved {len(paginated_alerts)} alerts",
            alerts=paginated_alerts,
            total=total
        )
    
    def _apply_filters(self, alerts: List[Alert], query: AlertQuery) -> List[Alert]:
        """Apply query filters to alerts list."""
        
        filtered = alerts
        
        # Filter by status
        if query.status:
            filtered = [a for a in filtered if a.status in query.status]
        
        # Filter by severity
        if query.severity:
            filtered = [a for a in filtered if a.severity in query.severity]
        
        # Filter by source
        if query.source:
            filtered = [a for a in filtered if a.source in query.source]
        
        # Filter by assignee
        if query.assignee:
            filtered = [a for a in filtered if a.assignee == query.assignee]
        
        # Filter by labels
        if query.labels:
            filtered = [
                a for a in filtered 
                if all(a.labels.get(k) == v for k, v in query.labels.items())
            ]
        
        # Filter by time range
        if query.from_time:
            filtered = [a for a in filtered if a.timestamp >= query.from_time]
        
        if query.to_time:
            filtered = [a for a in filtered if a.timestamp <= query.to_time]
        
        return filtered
    
    def _apply_sorting(self, alerts: List[Alert], sort_by: str, sort_order: str) -> List[Alert]:
        """Apply sorting to alerts list."""
        
        reverse = sort_order == "desc"
        
        if sort_by == "timestamp":
            return sorted(alerts, key=lambda a: a.timestamp, reverse=reverse)
        elif sort_by == "severity":
            # Define severity order for sorting
            severity_order = {
                SeverityLevel.CRITICAL: 5,
                SeverityLevel.HIGH: 4,
                SeverityLevel.MEDIUM: 3,
                SeverityLevel.LOW: 2,
                SeverityLevel.INFO: 1
            }
            return sorted(alerts, key=lambda a: severity_order.get(a.severity, 0), reverse=reverse)
        elif sort_by == "title":
            return sorted(alerts, key=lambda a: a.title.lower(), reverse=reverse)
        elif sort_by == "status":
            return sorted(alerts, key=lambda a: a.status.value, reverse=reverse)
        else:
            # Default to timestamp
            return sorted(alerts, key=lambda a: a.timestamp, reverse=reverse)
    
    async def get_alert_statistics(self, tenant_id: str) -> AlertStatistics:
        """
        Get alert statistics for a tenant.
        
        Args:
            tenant_id: Tenant ID for data isolation
            
        Returns:
            Alert statistics
        """
        
        # Get tenant alerts
        tenant_alert_ids = self._tenant_alerts.get(tenant_id, set())
        alerts = [self._alerts[aid] for aid in tenant_alert_ids if aid in self._alerts]
        
        # Calculate statistics
        total = len(alerts)
        
        by_status = defaultdict(int)
        by_severity = defaultdict(int)
        by_source = defaultdict(int)
        
        resolution_times = []
        
        for alert in alerts:
            by_status[alert.status] += 1
            by_severity[alert.severity] += 1
            by_source[alert.source] += 1
            
            # Calculate resolution time for resolved alerts
            if alert.status == AlertStatus.RESOLVED and alert.ends_at:
                resolution_time = (alert.ends_at - alert.starts_at).total_seconds() / 60
                resolution_times.append(resolution_time)
        
        # Calculate average resolution time and MTTR
        resolution_time_avg = None
        mttr = None
        
        if resolution_times:
            resolution_time_avg = sum(resolution_times) / len(resolution_times)
            mttr = resolution_time_avg  # Simplified MTTR calculation
        
        return AlertStatistics(
            total=total,
            by_status=dict(by_status),
            by_severity=dict(by_severity),
            by_source=dict(by_source),
            resolution_time_avg=resolution_time_avg,
            mttr=mttr
        )
    
    async def create_silence(self, request: SilenceRequest, user_id: str, tenant_id: str) -> Silence:
        """
        Create a new silence.
        
        Args:
            request: Silence request parameters
            user_id: User creating the silence
            tenant_id: Tenant ID for isolation
            
        Returns:
            Created silence
        """
        
        silence_id = str(uuid.uuid4())
        
        silence = Silence(
            id=silence_id,
            matchers=request.matchers,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            created_by=user_id,
            comment=request.comment,
            status="active" if request.starts_at <= datetime.utcnow() <= request.ends_at else "pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self._silences[silence_id] = silence
        
        return silence
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health status of alert service.
        
        Returns:
            Health status dictionary
        """
        
        return {
            "alert_service": True,
            "deduplication": len(self._deduplicator._alert_fingerprints) >= 0,
            "grouping": len(self._grouper._groups) >= 0,
            "storage": len(self._alerts) >= 0
        }