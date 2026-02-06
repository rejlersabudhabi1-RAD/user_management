"""
Real-time Activity Tracking Models.

Track all user and system activities in real-time for monitoring and audit purposes.

IMPORTANT: Extracted from main application - maintain backward compatibility.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class SystemActivity(models.Model):
    """
    Track all system activities in real-time.
    
    Features:
    - Soft-coded activity types and categories
    - User context tracking
    - Generic foreign keys for any object
    - Performance metrics
    - Severity levels for alerting
    
    Usage:
        >>> SystemActivity.objects.create(
        ...     activity_type='user_login',
        ...     user=user,
        ...     description='User logged in',
        ...     ip_address='192.168.1.1'
        ... )
    """
    
    ACTIVITY_TYPES = [
        ('user_login', 'User Login'),
        ('user_logout', 'User Logout'),
        ('user_created', 'User Created'),
        ('user_updated', 'User Updated'),
        ('user_deleted', 'User Deleted'),
        ('role_assigned', 'Role Assigned'),
        ('role_removed', 'Role Removed'),
        ('permission_granted', 'Permission Granted'),
        ('permission_revoked', 'Permission Revoked'),
        ('document_uploaded', 'Document Uploaded'),
        ('document_processed', 'Document Processed'),
        ('document_deleted', 'Document Deleted'),
        ('project_created', 'Project Created'),
        ('project_updated', 'Project Updated'),
        ('project_deleted', 'Project Deleted'),
        ('api_request', 'API Request'),
        ('system_error', 'System Error'),
        ('security_event', 'Security Event'),
        ('data_export', 'Data Export'),
        ('data_import', 'Data Import'),
        ('backup_created', 'Backup Created'),
        ('settings_changed', 'Settings Changed'),
        ('notification_sent', 'Notification Sent'),
        ('report_generated', 'Report Generated'),
        ('ai_analysis', 'AI Analysis Completed'),
        ('ml_prediction', 'ML Prediction Made'),
        ('database_query', 'Database Query'),
        ('cache_hit', 'Cache Hit'),
        ('cache_miss', 'Cache Miss'),
        ('webhook_triggered', 'Webhook Triggered'),
    ]
    
    ACTIVITY_CATEGORIES = [
        ('authentication', 'Authentication'),
        ('authorization', 'Authorization'),
        ('data_management', 'Data Management'),
        ('system_operation', 'System Operation'),
        ('security', 'Security'),
        ('api', 'API'),
        ('ml_ai', 'ML/AI'),
        ('communication', 'Communication'),
        ('maintenance', 'Maintenance'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Core fields
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPES,
        db_index=True,
        help_text="Type of activity being tracked"
    )
    category = models.CharField(
        max_length=50,
        choices=ACTIVITY_CATEGORIES,
        default='system_operation',
        help_text="Category for grouping activities"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='normal',
        help_text="Severity level for alerting"
    )
    
    # User and context
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        help_text="User who performed the activity"
    )
    user_email = models.EmailField(
        blank=True,
        help_text="User email at time of activity"
    )
    user_full_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="User full name at time of activity"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Client user agent string"
    )
    
    # Activity details
    description = models.TextField(
        help_text="Human-readable description of the activity"
    )
    details = models.JSONField(
        default=dict,
        help_text="Additional activity details in JSON format"
    )
    
    # Related object (generic foreign key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Status
    success = models.BooleanField(
        default=True,
        help_text="Whether the activity completed successfully"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if activity failed"
    )
    
    # Performance metrics
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration in milliseconds"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata"
    )
    tags = models.JSONField(
        default=list,
        help_text="Tags for categorization"
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the activity occurred"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_activity'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'activity_type']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['category', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
        ]
        verbose_name = 'System Activity'
        verbose_name_plural = 'System Activities'
    
    def __str__(self):
        return f"{self.activity_type} by {self.user_email or 'System'} at {self.timestamp}"
    
    @property
    def time_ago(self):
        """Human-readable time since activity"""
        now = timezone.now()
        diff = now - self.timestamp
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds/60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds/3600)}h ago"
        else:
            return f"{int(seconds/86400)}d ago"


class ActivityStream(models.Model):
    """
    Aggregated activity stream for dashboard.
    
    Pre-processed for fast retrieval and display.
    Denormalized data for performance.
    """
    
    activity = models.OneToOneField(
        SystemActivity,
        on_delete=models.CASCADE,
        related_name='stream'
    )
    
    # Display fields (denormalized for performance)
    display_title = models.CharField(
        max_length=500,
        help_text="Title to display in activity feed"
    )
    display_subtitle = models.CharField(
        max_length=500,
        blank=True,
        help_text="Subtitle for additional context"
    )
    icon = models.CharField(
        max_length=50,
        default='info',
        help_text="Icon name for display"
    )
    color = models.CharField(
        max_length=50,
        default='blue',
        help_text="Color for display"
    )
    
    # Grouping
    is_grouped = models.BooleanField(
        default=False,
        help_text="Whether this is a grouped activity"
    )
    group_key = models.CharField(
        max_length=200,
        blank=True,
        db_index=True,
        help_text="Key for grouping similar activities"
    )
    group_count = models.IntegerField(
        default=1,
        help_text="Number of activities in this group"
    )
    
    # Visibility
    is_public = models.BooleanField(
        default=True,
        help_text="Whether activity is public"
    )
    is_pinned = models.BooleanField(
        default=False,
        help_text="Whether activity is pinned to top"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_stream'
        ordering = ['-created_at']
        verbose_name = 'Activity Stream'
        verbose_name_plural = 'Activity Streams'


class ActivityStatistics(models.Model):
    """
    Real-time activity statistics.
    
    Updated periodically for dashboard display.
    Provides aggregated metrics for reporting.
    """
    
    PERIOD_TYPES = [
        ('minute', 'Minute'),
        ('hour', 'Hour'),
        ('day', 'Day'),
    ]
    
    # Time period
    period_start = models.DateTimeField(
        help_text="Start of the time period"
    )
    period_end = models.DateTimeField(
        help_text="End of the time period"
    )
    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_TYPES,
        help_text="Type of time period"
    )
    
    # Activity counts by type
    total_activities = models.IntegerField(
        default=0,
        help_text="Total number of activities"
    )
    user_activities = models.IntegerField(
        default=0,
        help_text="Activities initiated by users"
    )
    system_activities = models.IntegerField(
        default=0,
        help_text="Activities initiated by system"
    )
    api_requests = models.IntegerField(
        default=0,
        help_text="Number of API requests"
    )
    
    # Activities by category
    activities_by_category = models.JSONField(
        default=dict,
        help_text="Count of activities by category"
    )
    activities_by_type = models.JSONField(
        default=dict,
        help_text="Count of activities by type"
    )
    
    # Top users
    top_users = models.JSONField(
        default=list,
        help_text="List of most active users"
    )
    
    # Performance
    avg_duration_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="Average activity duration in milliseconds"
    )
    success_rate = models.FloatField(
        default=100.0,
        help_text="Percentage of successful activities"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional statistical metadata"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_statistics'
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['period_type', '-period_start']),
        ]
        verbose_name = 'Activity Statistics'
        verbose_name_plural = 'Activity Statistics'


class UserSession(models.Model):
    """
    Track active user sessions for real-time presence.
    
    Monitors online users and their current activity.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions',
        help_text="User associated with this session"
    )
    session_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique session identifier"
    )
    
    # Session info
    ip_address = models.GenericIPAddressField(
        help_text="Client IP address"
    )
    user_agent = models.TextField(
        help_text="Client user agent string"
    )
    device_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Device type (desktop, mobile, tablet)"
    )
    browser = models.CharField(
        max_length=100,
        blank=True,
        help_text="Browser name and version"
    )
    os = models.CharField(
        max_length=100,
        blank=True,
        help_text="Operating system"
    )
    
    # Activity
    last_activity = models.DateTimeField(
        default=timezone.now,
        help_text="Last activity timestamp"
    )
    current_page = models.CharField(
        max_length=500,
        blank=True,
        help_text="Current page/route user is viewing"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether session is currently active"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="When the session expires"
    )
    
    class Meta:
        db_table = 'user_session'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['is_active', '-last_activity']),
        ]
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
    
    def __str__(self):
        return f"{self.user.email} - {self.session_key[:8]}"
    
    @property
    def is_expired(self):
        """Check if session has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def duration(self):
        """Get session duration in seconds"""
        return (self.last_activity - self.created_at).total_seconds()
