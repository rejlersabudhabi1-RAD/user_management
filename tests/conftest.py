"""
Pytest configuration and fixtures for user_management tests.
"""
import pytest
from django.conf import settings


def pytest_configure():
    """Configure Django settings for tests"""
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'rest_framework',
                'user_management.core',
                'user_management.authentication',
                'user_management.authorization',
                'user_management.activity',
            ],
            AUTH_USER_MODEL='authentication.User',
            SECRET_KEY='test-secret-key-for-testing-only',
            USE_TZ=True,
            REST_FRAMEWORK={
                'DEFAULT_AUTHENTICATION_CLASSES': [
                    'rest_framework_simplejwt.authentication.JWTAuthentication',
                ],
                'DEFAULT_PERMISSION_CLASSES': [
                    'rest_framework.permissions.IsAuthenticated',
                ],
            }
        )
        
        # Setup Django
        import django
        django.setup()


@pytest.fixture
def test_user(db):
    """Fixture for creating a test user"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_organization(db):
    """Fixture for creating a test organization"""
    from user_management.authorization.models import Organization
    
    return Organization.objects.create(
        name='Test Organization',
        code='TEST_ORG',
        description='Test organization for testing'
    )


@pytest.fixture
def test_module(db):
    """Fixture for creating a test module"""
    from user_management.authorization.models import Module
    
    return Module.objects.create(
        name='PID Analysis',
        code='PID',
        description='P&ID verification module'
    )


@pytest.fixture
def test_role(db):
    """Fixture for creating a test role"""
    from user_management.authorization.models import Role
    
    return Role.objects.create(
        name='Test User',
        code='test_user',
        level=4,
        description='Test user role'
    )


@pytest.fixture
def admin_user(db, test_organization):
    """Fixture for creating an admin user with RBAC profile"""
    from django.contrib.auth import get_user_model
    from user_management.authorization.models import Role, UserProfile, UserRole
    
    User = get_user_model()
    
    user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )
    
    # Create admin role
    admin_role = Role.objects.create(
        name='Admin',
        code='admin',
        level=2,
        description='Administrator role'
    )
    
    # Create user profile
    profile = UserProfile.objects.create(
        user=user,
        organization=test_organization,
        status='active'
    )
    
    # Assign role
    UserRole.objects.create(
        user=user,
        role=admin_role,
        is_primary=True
    )
    
    return user


@pytest.fixture
def api_client():
    """Fixture for DRF API client"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Fixture for authenticated API client"""
    api_client.force_authenticate(user=test_user)
    return api_client
