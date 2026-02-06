"""
Tests for Activity Tracking Module.

Comprehensive test coverage for activity tracking functionality.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from user_management.activity.models import (
    SystemActivity, ActivityStream, ActivityStatistics, UserSession
)
from user_management.activity.tracker import ActivityTracker

User = get_user_model()


@pytest.mark.django_db
class TestSystemActivity:
    """Test cases for SystemActivity model"""
    
    def test_create_activity(self):
        """Test creating a system activity"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        activity = SystemActivity.objects.create(
            activity_type='user_login',
            category='authentication',
            severity='normal',
            user=user,
            user_email=user.email,
            description='User logged in successfully',
            success=True
        )
        
        assert activity.activity_type == 'user_login'
        assert activity.category == 'authentication'
        assert activity.user == user
        assert activity.success
    
    def test_activity_time_ago(self):
        """Test time_ago property"""
        activity = SystemActivity.objects.create(
            activity_type='user_login',
            description='Test activity',
            timestamp=timezone.now() - timedelta(minutes=5)
        )
        
        assert 'm ago' in activity.time_ago
    
    def test_activity_with_details(self):
        """Test activity with JSON details"""
        activity = SystemActivity.objects.create(
            activity_type='api_request',
            category='api',
            description='API request',
            details={
                'method': 'GET',
                'path': '/api/users/',
                'status_code': 200
            },
            duration_ms=150
        )
        
        assert activity.details['method'] == 'GET'
        assert activity.duration_ms == 150
    
    def test_activity_with_tags(self):
        """Test activity with tags"""
        activity = SystemActivity.objects.create(
            activity_type='document_uploaded',
            category='data_management',
            description='Document uploaded',
            tags=['pid', 'analysis', 'important']
        )
        
        assert len(activity.tags) == 3
        assert 'pid' in activity.tags


@pytest.mark.django_db
class TestActivityStream:
    """Test cases for ActivityStream model"""
    
    def test_create_activity_stream(self):
        """Test creating an activity stream"""
        activity = SystemActivity.objects.create(
            activity_type='user_login',
            description='User logged in'
        )
        
        stream = ActivityStream.objects.create(
            activity=activity,
            display_title='User Login',
            display_subtitle='test@example.com',
            icon='login',
            color='green'
        )
        
        assert stream.activity == activity
        assert stream.display_title == 'User Login'
        assert stream.icon == 'login'
    
    def test_grouped_activity(self):
        """Test grouped activity stream"""
        activity = SystemActivity.objects.create(
            activity_type='api_request',
            description='API request'
        )
        
        stream = ActivityStream.objects.create(
            activity=activity,
            display_title='API Requests',
            is_grouped=True,
            group_key='api_requests_5min',
            group_count=15
        )
        
        assert stream.is_grouped
        assert stream.group_count == 15


@pytest.mark.django_db
class TestActivityStatistics:
    """Test cases for ActivityStatistics model"""
    
    def test_create_statistics(self):
        """Test creating activity statistics"""
        now = timezone.now()
        
        stats = ActivityStatistics.objects.create(
            period_start=now - timedelta(hours=1),
            period_end=now,
            period_type='hour',
            total_activities=100,
            user_activities=80,
            system_activities=20,
            activities_by_category={
                'authentication': 30,
                'api': 50,
                'data_management': 20
            },
            success_rate=95.5
        )
        
        assert stats.total_activities == 100
        assert stats.success_rate == 95.5
        assert stats.activities_by_category['api'] == 50


@pytest.mark.django_db
class TestUserSession:
    """Test cases for UserSession model"""
    
    def test_create_session(self):
        """Test creating a user session"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        now = timezone.now()
        session = UserSession.objects.create(
            user=user,
            session_key='test_session_key_123',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            device_type='Desktop',
            browser='Chrome',
            os='Windows',
            is_active=True,
            expires_at=now + timedelta(hours=24)
        )
        
        assert session.user == user
        assert session.device_type == 'Desktop'
        assert session.is_active
    
    def test_session_is_expired(self):
        """Test session expiry check"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Expired session
        session = UserSession.objects.create(
            user=user,
            session_key='expired_session',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        assert session.is_expired
    
    def test_session_duration(self):
        """Test session duration calculation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        session = UserSession.objects.create(
            user=user,
            session_key='test_session',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Duration should be close to 0 for new session
        assert session.duration >= 0


@pytest.mark.django_db
class TestActivityTracker:
    """Test cases for ActivityTracker utility"""
    
    def test_track_activity(self):
        """Test tracking an activity"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        activity = ActivityTracker.track(
            activity_type='user_login',
            user=user,
            description='User logged in',
            category='authentication',
            severity='normal',
            success=True
        )
        
        assert activity is not None
        assert activity.user == user
        assert activity.activity_type == 'user_login'
    
    def test_parse_user_agent(self):
        """Test user agent parsing"""
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        info = ActivityTracker.parse_user_agent(user_agent)
        
        assert info['device'] == 'Desktop'
        assert info['browser'] == 'Chrome'
        assert info['os'] == 'Windows'
    
    def test_parse_mobile_user_agent(self):
        """Test parsing mobile user agent"""
        user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
        
        info = ActivityTracker.parse_user_agent(user_agent)
        
        assert info['device'] == 'Mobile'
        assert info['os'] == 'iOS'
    
    def test_get_active_users(self):
        """Test getting active users"""
        user1 = User.objects.create_user(username='user1', email='user1@example.com', password='pass')
        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass')
        
        # Active session
        UserSession.objects.create(
            user=user1,
            session_key='active_session',
            ip_address='192.168.1.1',
            user_agent='Mozilla',
            is_active=True,
            last_activity=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Inactive session (old activity)
        UserSession.objects.create(
            user=user2,
            session_key='inactive_session',
            ip_address='192.168.1.2',
            user_agent='Mozilla',
            is_active=True,
            last_activity=timezone.now() - timedelta(minutes=10),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        active_users = ActivityTracker.get_active_users()
        assert active_users.count() == 1
    
    def test_get_recent_activities(self):
        """Test getting recent activities"""
        user = User.objects.create_user(username='user', email='user@example.com', password='pass')
        
        # Create multiple activities
        for i in range(10):
            SystemActivity.objects.create(
                activity_type='api_request',
                user=user,
                category='api',
                description=f'Request {i}'
            )
        
        activities = ActivityTracker.get_recent_activities(limit=5, user=user)
        assert len(activities) == 5
    
    def test_get_recent_activities_by_category(self):
        """Test filtering activities by category"""
        user = User.objects.create_user(username='user', email='user@example.com', password='pass')
        
        SystemActivity.objects.create(
            activity_type='user_login',
            user=user,
            category='authentication',
            description='Login'
        )
        
        SystemActivity.objects.create(
            activity_type='api_request',
            user=user,
            category='api',
            description='API call'
        )
        
        activities = ActivityTracker.get_recent_activities(category='authentication')
        assert len(activities) == 1
        assert activities[0].category == 'authentication'
