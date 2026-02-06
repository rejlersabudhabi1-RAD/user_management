"""
Tests for Authentication Module.

Comprehensive test coverage for authentication functionality.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from user_management.authentication.models import User, UserProfile
from user_management.authentication.password_reset_service import PasswordResetService

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test cases for User model"""
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        assert user.is_staff
        assert user.is_superuser
    
    def test_user_str(self):
        """Test user string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert str(user) == 'test@example.com'


@pytest.mark.django_db
class TestUserProfile:
    """Test cases for UserProfile model"""
    
    def test_create_profile(self):
        """Test creating a user profile"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            phone='1234567890',
            status='active'
        )
        
        assert profile.user == user
        assert profile.phone == '1234567890'
        assert profile.status == 'active'
    
    def test_profile_soft_delete(self):
        """Test soft delete functionality"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        profile = UserProfile.objects.create(user=user)
        profile.delete()
        
        # Profile should still exist but be marked as deleted
        profile.refresh_from_db()
        assert profile.deleted_at is not None
        assert profile.is_deleted


@pytest.mark.django_db
class TestPasswordResetService:
    """Test cases for PasswordResetService"""
    
    def test_create_reset_token(self):
        """Test creating a password reset token"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        service = PasswordResetService()
        token = service.create_reset_token(user)
        
        assert token is not None
        assert len(token) > 0
        
        # Verify token is stored
        user.refresh_from_db()
        assert user.password_reset_token is not None
    
    def test_verify_reset_token_valid(self):
        """Test verifying a valid reset token"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        service = PasswordResetService()
        token = service.create_reset_token(user)
        
        # Verify token
        verified_user = service.verify_reset_token(token)
        assert verified_user == user
    
    def test_verify_reset_token_expired(self):
        """Test verifying an expired token"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        service = PasswordResetService()
        token = service.create_reset_token(user)
        
        # Manually expire the token
        user.password_reset_expires = timezone.now() - timedelta(hours=1)
        user.save()
        
        # Verify token should fail
        verified_user = service.verify_reset_token(token)
        assert verified_user is None
    
    def test_clear_reset_token(self):
        """Test clearing a reset token"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        service = PasswordResetService()
        service.create_reset_token(user)
        
        # Clear token
        service.clear_reset_token(user)
        
        user.refresh_from_db()
        assert user.password_reset_token is None
        assert user.password_reset_expires is None


@pytest.mark.django_db
class TestPasswordPolicy:
    """Test cases for password policy enforcement"""
    
    def test_password_expiry(self):
        """Test password expiry tracking"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Set password expiry to past
        user.password_expires_at = timezone.now() - timedelta(days=1)
        user.save()
        
        # Check if password is expired
        assert user.password_expires_at < timezone.now()
    
    def test_failed_login_tracking(self):
        """Test failed login attempt tracking"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Simulate failed login attempts
        user.failed_login_attempts = 3
        user.save()
        
        assert user.failed_login_attempts == 3
