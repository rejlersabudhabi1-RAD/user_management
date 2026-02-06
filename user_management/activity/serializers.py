"""
Activity Tracking Serializers.

DRF serializers for activity tracking API endpoints.

IMPORTANT: Extracted from main application - maintain backward compatibility.
"""
from rest_framework import serializers
from .models import SystemActivity, ActivityStream, ActivityStatistics, UserSession


class SystemActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for SystemActivity model.
    
    Includes computed fields for user information and duration.
    """
    
    user_name = serializers.SerializerMethodField()
    user_email_field = serializers.SerializerMethodField()
    time_ago = serializers.ReadOnlyField()
    
    class Meta:
        model = SystemActivity
        fields = [
            'id',
            'activity_type',
            'category',
            'severity',
            'description',
            'user',
            'user_name',
            'user_email',
            'user_email_field',
            'user_full_name',
            'ip_address',
            'user_agent',
            'details',
            'success',
            'error_message',
            'duration_ms',
            'metadata',
            'tags',
            'timestamp',
            'time_ago',
            'created_at',
        ]
        read_only_fields = ['id', 'timestamp', 'created_at', 'time_ago']
    
    def get_user_name(self, obj):
        """Get user's full name or username"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return obj.user_full_name or 'System'
    
    def get_user_email_field(self, obj):
        """Get user's email from user object or stored field"""
        if obj.user:
            return obj.user.email
        return obj.user_email


class ActivityStreamSerializer(serializers.ModelSerializer):
    """
    Serializer for ActivityStream model.
    
    Includes nested activity data for display.
    """
    
    activity_type = serializers.CharField(source='activity.activity_type', read_only=True)
    timestamp = serializers.DateTimeField(source='activity.timestamp', read_only=True)
    
    class Meta:
        model = ActivityStream
        fields = [
            'id',
            'activity',
            'activity_type',
            'display_title',
            'display_subtitle',
            'icon',
            'color',
            'is_grouped',
            'group_key',
            'group_count',
            'is_public',
            'is_pinned',
            'timestamp',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ActivityStatisticsSerializer(serializers.ModelSerializer):
    """
    Serializer for ActivityStatistics model.
    
    Provides aggregated statistics for dashboard display.
    """
    
    period_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityStatistics
        fields = [
            'id',
            'period_start',
            'period_end',
            'period_type',
            'period_duration',
            'total_activities',
            'user_activities',
            'system_activities',
            'api_requests',
            'activities_by_category',
            'activities_by_type',
            'top_users',
            'avg_duration_ms',
            'success_rate',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_period_duration(self, obj):
        """Get period duration in seconds"""
        return (obj.period_end - obj.period_start).total_seconds()


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserSession model.
    
    Includes computed fields for user information and session metrics.
    """
    
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    session_duration = serializers.ReadOnlyField(source='duration')
    is_expired_field = serializers.ReadOnlyField(source='is_expired')
    
    class Meta:
        model = UserSession
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'session_key',
            'ip_address',
            'user_agent',
            'device_type',
            'browser',
            'os',
            'last_activity',
            'current_page',
            'is_active',
            'is_expired_field',
            'created_at',
            'expires_at',
            'session_duration',
        ]
        read_only_fields = ['id', 'created_at', 'session_duration', 'is_expired_field']
    
    def get_user_name(self, obj):
        """Get user's full name or username"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None
    
    def get_user_email(self, obj):
        """Get user's email"""
        if obj.user:
            return obj.user.email
        return None


class ActivitySummarySerializer(serializers.Serializer):
    """
    Serializer for activity summary statistics.
    
    Used for dashboard summary endpoints.
    """
    
    total_last_hour = serializers.IntegerField(
        help_text="Total activities in the last hour"
    )
    total_last_24h = serializers.IntegerField(
        help_text="Total activities in the last 24 hours"
    )
    by_category = serializers.DictField(
        help_text="Activity counts by category"
    )
    by_severity = serializers.DictField(
        help_text="Activity counts by severity"
    )
    success_rate = serializers.FloatField(
        help_text="Percentage of successful activities"
    )
    average_duration = serializers.FloatField(
        help_text="Average activity duration in milliseconds"
    )
    active_users = serializers.IntegerField(
        help_text="Number of currently active users"
    )
    top_activities = serializers.ListField(
        help_text="Top activity types by count"
    )
