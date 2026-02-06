"""
Activity Tracking Views.

DRF ViewSets for activity tracking API endpoints.

IMPORTANT: Extracted from main application - maintain backward compatibility.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta
import logging

from .models import SystemActivity, ActivityStream, ActivityStatistics, UserSession
from .serializers import (
    SystemActivitySerializer,
    ActivityStreamSerializer,
    ActivityStatisticsSerializer,
    UserSessionSerializer,
    ActivitySummarySerializer,
)

logger = logging.getLogger(__name__)


class SystemActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing system activities.
    
    Provides read-only access to activity logs with filtering and statistics.
    
    Endpoints:
    - list: Get paginated list of activities
    - retrieve: Get single activity detail
    - recent: Get recent activities
    - statistics: Get aggregated statistics
    - by_user: Get activities grouped by user
    """
    queryset = SystemActivity.objects.all()
    serializer_class = SystemActivitySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['activity_type', 'category', 'severity', 'success', 'user']
    search_fields = ['description', 'user__username', 'user__email', 'user_email']
    ordering_fields = ['timestamp', 'severity', 'activity_type']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter activities based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filter by time range (hours)
        hours = self.request.query_params.get('hours')
        if hours:
            try:
                hours = int(hours)
                cutoff = timezone.now() - timedelta(hours=hours)
                queryset = queryset.filter(timestamp__gte=cutoff)
            except ValueError:
                pass
        
        return queryset.select_related('user')
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent activities.
        
        Query Parameters:
        - limit: Number of activities (default: 50, max: 200)
        - category: Filter by category
        """
        limit = min(int(request.query_params.get('limit', 50)), 200)
        category = request.query_params.get('category')
        
        queryset = self.get_queryset()
        
        if category and category != 'all':
            queryset = queryset.filter(category=category)
        
        activities = queryset[:limit]
        serializer = self.get_serializer(activities, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get activity statistics.
        
        Returns aggregated statistics for the last 24 hours.
        """
        now = timezone.now()
        
        # Last hour
        last_hour = now - timedelta(hours=1)
        total_last_hour = SystemActivity.objects.filter(
            timestamp__gte=last_hour
        ).count()
        
        # Last 24 hours
        last_24h = now - timedelta(hours=24)
        activities_24h = SystemActivity.objects.filter(
            timestamp__gte=last_24h
        )
        total_last_24h = activities_24h.count()
        
        # By category
        by_category = dict(
            activities_24h.values('category')
            .annotate(count=Count('id'))
            .values_list('category', 'count')
        )
        
        # By severity
        by_severity = dict(
            activities_24h.values('severity')
            .annotate(count=Count('id'))
            .values_list('severity', 'count')
        )
        
        # Success rate
        total_activities = activities_24h.count()
        success_count = activities_24h.filter(success=True).count()
        success_rate = (success_count / total_activities * 100) if total_activities > 0 else 100.0
        
        # Average duration
        avg_duration = activities_24h.exclude(
            duration_ms__isnull=True
        ).aggregate(Avg('duration_ms'))['duration_ms__avg'] or 0
        
        # Active users (sessions)
        active_users = UserSession.objects.filter(is_active=True).count()
        
        # Top activities
        top_activities = list(
            activities_24h.values('activity_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
            .values('activity_type', 'count')
        )
        
        data = {
            'total_last_hour': total_last_hour,
            'total_last_24h': total_last_24h,
            'by_category': by_category,
            'by_severity': by_severity,
            'success_rate': round(success_rate, 2),
            'average_duration': round(avg_duration, 2),
            'active_users': active_users,
            'top_activities': top_activities,
        }
        
        serializer = ActivitySummarySerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """
        Get activities grouped by user.
        
        Query Parameters:
        - hours: Time range in hours (default: 24)
        
        Returns top 20 most active users.
        """
        hours = int(request.query_params.get('hours', 24))
        cutoff = timezone.now() - timedelta(hours=hours)
        
        activities = (
            SystemActivity.objects.filter(timestamp__gte=cutoff)
            .values('user__username', 'user__email')
            .annotate(
                total=Count('id'),
                success=Count('id', filter=Q(success=True)),
                failure=Count('id', filter=Q(success=False)),
            )
            .order_by('-total')[:20]
        )
        
        return Response(list(activities))


class ActivityStreamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing activity streams.
    
    Provides CRUD operations for activity stream configurations.
    """
    queryset = ActivityStream.objects.all()
    serializer_class = ActivityStreamSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_grouped', 'is_public', 'is_pinned']
    ordering = ['-created_at']


class ActivityStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing activity statistics.
    
    Read-only access to pre-calculated statistics.
    """
    queryset = ActivityStatistics.objects.all()
    serializer_class = ActivityStatisticsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['period_type']
    ordering = ['-period_start']
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the latest statistics for each period type"""
        stats = {
            'minute': ActivityStatistics.objects.filter(period_type='minute').order_by('-period_start').first(),
            'hour': ActivityStatistics.objects.filter(period_type='hour').order_by('-period_start').first(),
            'day': ActivityStatistics.objects.filter(period_type='day').order_by('-period_start').first(),
        }
        
        result = {}
        for period_type, stat in stats.items():
            if stat:
                result[period_type] = self.get_serializer(stat).data
        
        return Response(result)


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user sessions.
    
    Monitor active sessions and user presence.
    """
    queryset = UserSession.objects.all()
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'is_active', 'device_type', 'browser']
    ordering = ['-last_activity']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active sessions"""
        sessions = self.queryset.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('user')
        
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_sessions(self, request):
        """Get current user's sessions"""
        sessions = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
