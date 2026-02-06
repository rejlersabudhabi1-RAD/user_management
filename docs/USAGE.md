# Usage Examples

Complete examples for using the User Management System.

## Table of Contents

- [Authentication](#authentication)
- [Authorization (RBAC)](#authorization-rbac)
- [Activity Tracking](#activity-tracking)
- [Django Integration](#django-integration)

## Authentication

### User Registration

```python
from user_management.authentication.serializers import UserRegistrationSerializer

# In your view
data = {
    'username': 'johndoe',
    'email': 'john@example.com',
    'password': 'SecurePass123!',
    'first_name': 'John',
    'last_name': 'Doe'
}

serializer = UserRegistrationSerializer(data=data)
if serializer.is_valid():
    user = serializer.save()
    print(f"User created: {user.email}")
```

### Password Reset Flow

```python
from user_management.authentication.password_reset_service import PasswordResetService
from django.contrib.auth import get_user_model

User = get_user_model()
service = PasswordResetService()

# Step 1: User requests password reset
user = User.objects.get(email='user@example.com')
token = service.create_reset_token(user)

# Step 2: Send email (handled by service)
service.send_password_reset_email(user, token, reset_url="https://yourapp.com/reset")

# Step 3: User clicks link, you verify token
verified_user = service.verify_reset_token(token)
if verified_user:
    # Step 4: Allow password change
    verified_user.set_password('NewSecurePassword123!')
    verified_user.save()
    
    # Step 5: Clear token
    service.clear_reset_token(verified_user)
```

### JWT Authentication

```python
from rest_framework_simplejwt.views import TokenObtainPairView
from user_management.authentication.serializers_jwt import EmailTokenObtainPairSerializer

# In urls.py
from django.urls import path

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(serializer_class=EmailTokenObtainPairSerializer)),
]

# Client usage
import requests

response = requests.post('https://yourapp.com/api/token/', json={
    'email': 'user@example.com',
    'password': 'password123'
})

tokens = response.json()
access_token = tokens['access']
refresh_token = tokens['refresh']

# Use access token in subsequent requests
headers = {'Authorization': f'Bearer {access_token}'}
```

## Authorization (RBAC)

### Setting Up Organizations and Roles

```python
from user_management.authorization.models import Organization, Role, Module, Permission

# Create organization
org = Organization.objects.create(
    name='My Company',
    code='MY_COMPANY',
    description='Main organization',
    settings={
        'theme': 'dark',
        'features': ['analytics', 'reporting']
    }
)

# Create modules
pid_module = Module.objects.create(
    name='PID Analysis',
    code='PID',
    description='P&ID design verification',
    order=1
)

# Create permissions
permission = Permission.objects.create(
    module=pid_module,
    name='Create PID Analysis',
    code='pid.create',
    action='create',
    description='Permission to create PID analyses'
)

# Create role
engineer_role = Role.objects.create(
    name='Engineer',
    code='engineer',
    level=4,
    description='Engineering staff role'
)

# Assign permissions and modules to role
from user_management.authorization.models import RolePermission, RoleModule

RolePermission.objects.create(role=engineer_role, permission=permission)
RoleModule.objects.create(role=engineer_role, module=pid_module)
```

### Assigning Roles to Users

```python
from user_management.authorization.models import UserProfile, UserRole
from django.contrib.auth import get_user_model

User = get_user_model()

user = User.objects.get(email='engineer@example.com')

# Create RBAC profile
profile = UserProfile.objects.create(
    user=user,
    organization=org,
    status='active',
    metadata={
        'department': 'Engineering',
        'employee_id': 'ENG-001'
    }
)

# Assign role
UserRole.objects.create(
    user=user,
    role=engineer_role,
    is_primary=True
)
```

### Checking Permissions in Views

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from user_management.authorization.permissions import HasPermission, HasModuleAccess

class PIDAnalysisViewSet(viewsets.ModelViewSet):
    permission_classes = [HasPermission]
    permission_required = 'pid.create'
    
    def create(self, request):
        # User must have 'pid.create' permission
        # This is automatically checked by HasPermission
        ...

class PIDDashboardView(viewsets.ViewSet):
    permission_classes = [HasModuleAccess]
    module_required = 'PID'
    
    @action(detail=False)
    def stats(self, request):
        # User must have access to PID module
        ...
```

### Checking Permissions Programmatically

```python
# Get user profile
profile = request.user.rbac_profile

# Check specific permission
if profile.has_permission('pid.create'):
    # User can create PID analyses
    pass

# Check module access
if profile.has_module_access('PID'):
    # User has access to PID module
    pass

# Get all user permissions
permissions = profile.get_all_permissions()
permission_codes = [p.code for p in permissions]

# Get all accessible modules
modules = profile.get_all_modules()
module_codes = [m.code for m in modules]
```

### Using RBAC Middleware

```python
# In settings.py
MIDDLEWARE = [
    ...
    'user_management.authorization.middleware.RBACMiddleware',
    'user_management.authorization.middleware.LoginTrackingMiddleware',
]

# The middleware automatically:
# 1. Attaches user_profile to request
# 2. Checks account status (active/suspended)
# 3. Enforces account locks
# 4. Logs write operations for audit
```

## Activity Tracking

### Manual Activity Tracking

```python
from user_management.activity.tracker import ActivityTracker

# Track user action
ActivityTracker.track(
    activity_type='document_uploaded',
    user=request.user,
    description='User uploaded PID drawing',
    category='data_management',
    severity='normal',
    success=True,
    details={
        'filename': 'drawing_001.pdf',
        'size_bytes': 1024000
    },
    tags=['pid', 'upload'],
    request=request
)

# Track system operation
ActivityTracker.track(
    activity_type='backup_created',
    description='Daily backup completed',
    category='maintenance',
    severity='normal',
    success=True,
    details={
        'backup_size': '2.5GB',
        'duration': '15 minutes'
    }
)
```

### Using Activity Tracking Decorator

```python
from user_management.activity.tracker import track_activity

@track_activity('document_processed', 'Document processing completed', 'data_management')
def process_document(document, request):
    # Your document processing logic
    # Activity is automatically tracked with timing
    ...
```

### Using Activity Middleware

```python
# In settings.py
MIDDLEWARE = [
    ...
    'user_management.activity.tracker.ActivityMiddleware',
]

# The middleware automatically:
# 1. Tracks all API requests with timing
# 2. Updates user sessions
# 3. Records IP addresses and user agents
```

### Querying Activities

```python
from user_management.activity.models import SystemActivity
from django.utils import timezone
from datetime import timedelta

# Get recent activities
recent = SystemActivity.objects.filter(
    timestamp__gte=timezone.now() - timedelta(hours=24)
).select_related('user')

# Get failed activities
failures = SystemActivity.objects.filter(
    success=False,
    severity__in=['high', 'critical']
)

# Get activities by category
auth_activities = SystemActivity.objects.filter(
    category='authentication'
)

# Get user's activities
user_activities = SystemActivity.objects.filter(
    user=request.user
).order_by('-timestamp')[:50]
```

### Monitoring Active Users

```python
from user_management.activity.tracker import ActivityTracker

# Get currently active users
active_users = ActivityTracker.get_active_users()

for session in active_users:
    print(f"{session.user.email} - {session.current_page}")
    print(f"  Device: {session.device_type} ({session.browser} on {session.os})")
    print(f"  Last active: {session.last_activity}")
```

## Django Integration

### Complete Settings Configuration

```python
# settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    
    # User Management System
    'user_management.core',
    'user_management.authentication',
    'user_management.authorization',
    'user_management.activity',
    
    # Your apps
    'myapp',
]

# Use custom user model
AUTH_USER_MODEL = 'authentication.User'

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # User Management Middleware
    'user_management.authorization.middleware.RBACMiddleware',
    'user_management.authorization.middleware.LoginTrackingMiddleware',
    'user_management.activity.tracker.ActivityMiddleware',
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# Simple JWT
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'TOKEN_OBTAIN_SERIALIZER': 'user_management.authentication.serializers_jwt.EmailTokenObtainPairSerializer',
}

# Email Configuration (for password reset)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@yourapp.com'
```

### URL Configuration

```python
# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user_management.activity.views import (
    SystemActivityViewSet,
    ActivityStreamViewSet,
    ActivityStatisticsViewSet,
    UserSessionViewSet
)

router = DefaultRouter()
router.register(r'activities', SystemActivityViewSet, basename='activity')
router.register(r'activity-streams', ActivityStreamViewSet, basename='activity-stream')
router.register(r'activity-stats', ActivityStatisticsViewSet, basename='activity-stats')
router.register(r'user-sessions', UserSessionViewSet, basename='user-session')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('user_management.api.urls')),
]
```

### Running Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Creating Initial Data

```python
# management/commands/setup_rbac.py

from django.core.management.base import BaseCommand
from user_management.authorization.models import Organization, Module, Role, Permission

class Command(BaseCommand):
    help = 'Setup initial RBAC data'
    
    def handle(self, *args, **options):
        # Create organization
        org, _ = Organization.objects.get_or_create(
            code='DEFAULT',
            defaults={
                'name': 'Default Organization',
                'description': 'Default organization'
            }
        )
        
        # Create modules
        modules = [
            ('PID', 'PID Analysis', 'P&ID design verification', 1),
            ('PFD', 'PFD Converter', 'PFD to P&ID conversion', 2),
            ('QHSE', 'QHSE Documents', 'QHSE document management', 3),
        ]
        
        for code, name, desc, order in modules:
            Module.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc, 'order': order}
            )
        
        # Create roles
        Role.objects.get_or_create(
            code='super_admin',
            defaults={'name': 'Super Admin', 'level': 1}
        )
        
        self.stdout.write(self.style.SUCCESS('RBAC setup completed!'))
```

## Advanced Examples

### Custom Permission Logic

```python
from rest_framework import permissions

class CanModifyOwnOrganizationOnly(permissions.BasePermission):
    """
    Custom permission: Users can only modify their own organization's data
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only if same organization
        try:
            user_org = request.user.rbac_profile.organization
            return obj.organization == user_org
        except:
            return False
```

### Background Activity Aggregation

```python
from celery import shared_task
from user_management.activity.models import SystemActivity, ActivityStatistics
from django.utils import timezone
from datetime import timedelta

@shared_task
def aggregate_hourly_statistics():
    """
    Aggregate activity statistics hourly
    """
    now = timezone.now()
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    hour_end = hour_start + timedelta(hours=1)
    
    activities = SystemActivity.objects.filter(
        timestamp__gte=hour_start,
        timestamp__lt=hour_end
    )
    
    stats = ActivityStatistics.objects.create(
        period_start=hour_start,
        period_end=hour_end,
        period_type='hour',
        total_activities=activities.count(),
        user_activities=activities.filter(user__isnull=False).count(),
        system_activities=activities.filter(user__isnull=True).count(),
        success_rate=activities.filter(success=True).count() / activities.count() * 100
    )
    
    return f"Aggregated {activities.count()} activities"
```
