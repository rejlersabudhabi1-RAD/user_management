# Migration Guide

Guide for migrating from the main AIFlow application to the extracted User Management System.

## Table of Contents

- [Overview](#overview)
- [Pre-Migration Checklist](#pre-migration-checklist)
- [Step-by-Step Migration](#step-by-step-migration)
- [Import Path Changes](#import-path-changes)
- [Database Migration](#database-migration)
- [Testing After Migration](#testing-after-migration)
- [Rollback Plan](#rollback-plan)

## Overview

This guide helps you migrate from the embedded user management code in AIFlow to the standalone `user_management` package.

**Migration Strategy**: Soft coding approach - no core logic changes, backward compatible.

**Timeline**: Estimated 2-4 hours for migration and testing.

## Pre-Migration Checklist

Before starting migration:

- [ ] **Backup database**: Create full database backup
- [ ] **Backup code**: Commit all changes to git
- [ ] **Document current state**: List all RBAC customizations
- [ ] **Test environment**: Verify test environment is working
- [ ] **Dependencies**: Check Python version (3.9+) and Django version (4.2+)
- [ ] **Review changes**: Read ARCHITECTURE.md and USAGE.md

## Step-by-Step Migration

### Step 1: Install the Package

```bash
# Option A: Install from GitHub (recommended during development)
cd /path/to/your/project
pip install -e /path/to/user_management

# Option B: Install from PyPI (when published)
pip install django-user-management-rbac
```

### Step 2: Update settings.py

```python
# settings.py

# OLD
INSTALLED_APPS = [
    ...
    'apps.authentication',
    'apps.rbac',
    'apps.activity',
]

AUTH_USER_MODEL = 'authentication.CustomUser'

MIDDLEWARE = [
    ...
    'apps.rbac.middleware.RBACMiddleware',
    'apps.activity.tracker.ActivityMiddleware',
]

# NEW
INSTALLED_APPS = [
    ...
    'user_management.core',
    'user_management.authentication',
    'user_management.authorization',
    'user_management.activity',
]

AUTH_USER_MODEL = 'authentication.User'  # Update if needed

MIDDLEWARE = [
    ...
    'user_management.authorization.middleware.RBACMiddleware',
    'user_management.authorization.middleware.LoginTrackingMiddleware',
    'user_management.activity.tracker.ActivityMiddleware',
]
```

### Step 3: Update Import Paths

Update all imports across your codebase:

```python
# OLD IMPORTS
from apps.authentication.models import CustomUser, UserProfile
from apps.rbac.models import Role, Permission, Organization
from apps.rbac.permissions import HasPermission, IsAdmin
from apps.rbac.middleware import RBACMiddleware
from apps.activity.models import SystemActivity
from apps.activity.tracker import ActivityTracker

# NEW IMPORTS
from user_management.authentication.models import User, UserProfile
from user_management.authorization.models import Role, Permission, Organization
from user_management.authorization.permissions import HasPermission, IsAdmin
from user_management.authorization.middleware import RBACMiddleware
from user_management.activity.models import SystemActivity
from user_management.activity.tracker import ActivityTracker
```

**Use find-and-replace** to update all imports:

```bash
# In your project directory
find . -name "*.py" -type f -exec sed -i 's/from apps\.authentication/from user_management.authentication/g' {} +
find . -name "*.py" -type f -exec sed -i 's/from apps\.rbac/from user_management.authorization/g' {} +
find . -name "*.py" -type f -exec sed -i 's/from apps\.activity/from user_management.activity/g' {} +
```

### Step 4: Update URLs

```python
# urls.py

# OLD
urlpatterns = [
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/rbac/', include('apps.rbac.urls')),
    path('api/v1/activity/', include('apps.activity.urls')),
]

# NEW
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
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('user_management.api.urls')),  # Create this if needed
]
```

### Step 5: Database Migration

#### Option A: Same Database (Recommended)

Keep existing data with table renames:

```sql
-- Backup first!
-- These commands rename tables to match new app labels

-- Authentication tables (if needed)
ALTER TABLE authentication_customuser RENAME TO authentication_user;

-- RBAC tables are unchanged (rbac_* → rbac_*)
-- Activity tables are unchanged (system_activity, etc.)

-- Update ContentType references
UPDATE django_content_type 
SET app_label = 'user_management.authentication' 
WHERE app_label = 'authentication';

UPDATE django_content_type 
SET app_label = 'user_management.authorization' 
WHERE app_label = 'rbac';

UPDATE django_content_type 
SET app_label = 'user_management.activity' 
WHERE app_label = 'activity';
```

#### Option B: Fresh Start

If starting fresh (dev/test environments):

```bash
# Drop old tables
python manage.py migrate authentication zero
python manage.py migrate rbac zero
python manage.py migrate activity zero

# Run new migrations
python manage.py migrate user_management.authentication
python manage.py migrate user_management.authorization
python manage.py migrate user_management.activity

# Create superuser
python manage.py createsuperuser

# Load initial data
python manage.py shell
>>> from user_management.authorization.models import Organization
>>> Organization.objects.create(name='Default Org', code='DEFAULT')
```

### Step 6: Update Model References

Update foreign key references in your models:

```python
# OLD
from django.conf import settings

class Document(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey('rbac.Organization', on_delete=models.CASCADE)

# NEW (same code, but verify imports)
from django.conf import settings

class Document(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey('authorization.Organization', on_delete=models.CASCADE)
```

### Step 7: Update Serializers

```python
# OLD
from apps.authentication.serializers import UserSerializer
from apps.rbac.serializers import RoleSerializer

# NEW
from user_management.authentication.serializers import UserSerializer
# Note: Create custom serializers for Role if needed
from user_management.authorization.models import Role
from rest_framework import serializers

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'level']
```

### Step 8: Update Views

```python
# OLD
from apps.rbac.permissions import HasPermission, HasModuleAccess

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [HasPermission]
    permission_required = 'feature.create'

# NEW (same code with updated import)
from user_management.authorization.permissions import HasPermission, HasModuleAccess

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [HasPermission]
    permission_required = 'feature.create'
```

### Step 9: Update Activity Tracking

```python
# OLD
from apps.activity.tracker import ActivityTracker

ActivityTracker.track(
    activity_type='document_uploaded',
    user=request.user,
    description='Document uploaded',
    request=request
)

# NEW (identical, just import change)
from user_management.activity.tracker import ActivityTracker

ActivityTracker.track(
    activity_type='document_uploaded',
    user=request.user,
    description='Document uploaded',
    request=request
)
```

## Import Path Changes

Complete mapping of import path changes:

### Authentication

| Old Path | New Path |
|----------|----------|
| `apps.authentication.models` | `user_management.authentication.models` |
| `apps.authentication.serializers` | `user_management.authentication.serializers` |
| `apps.authentication.services` | `user_management.authentication.password_reset_service` |

### Authorization (RBAC)

| Old Path | New Path |
|----------|----------|
| `apps.rbac.models` | `user_management.authorization.models` |
| `apps.rbac.permissions` | `user_management.authorization.permissions` |
| `apps.rbac.middleware` | `user_management.authorization.middleware` |
| `apps.rbac.utils` | `user_management.authorization.utils` |

### Activity Tracking

| Old Path | New Path |
|----------|----------|
| `apps.activity.models` | `user_management.activity.models` |
| `apps.activity.tracker` | `user_management.activity.tracker` |
| `apps.activity.views` | `user_management.activity.views` |
| `apps.activity.serializers` | `user_management.activity.serializers` |

## Database Migration

### Table Name Mapping

Most tables remain the same, making migration easier:

| Module | Old Table | New Table | Action |
|--------|-----------|-----------|--------|
| Users | `authentication_customuser` | `authentication_user` | Rename if needed |
| User Profile | `authentication_userprofile` | `authentication_userprofile` | No change |
| Organization | `rbac_organization` | `rbac_organization` | No change |
| Module | `rbac_module` | `rbac_module` | No change |
| Permission | `rbac_permission` | `rbac_permission` | No change |
| Role | `rbac_role` | `rbac_role` | No change |
| User Role | `rbac_userrole` | `rbac_userrole` | No change |
| Activities | `system_activity` | `system_activity` | No change |
| Sessions | `user_session` | `user_session` | No change |

### Migration Script

Use this script to safely migrate database:

```python
# migrate_database.py

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Migrate database tables for user_management package'
    
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Update ContentType app labels
            cursor.execute("""
                UPDATE django_content_type 
                SET app_label = 'user_management.authentication' 
                WHERE app_label = 'authentication'
            """)
            
            cursor.execute("""
                UPDATE django_content_type 
                SET app_label = 'user_management.authorization' 
                WHERE app_label = 'rbac'
            """)
            
            cursor.execute("""
                UPDATE django_content_type 
                SET app_label = 'user_management.activity' 
                WHERE app_label = 'activity'
            """)
            
            self.stdout.write(self.style.SUCCESS('Database migration completed!'))
```

## Testing After Migration

### 1. Run Tests

```bash
# Run all tests
python manage.py test

# Run user management tests
python manage.py test user_management

# Run with pytest
pytest tests/
```

### 2. Manual Testing Checklist

- [ ] **Login**: Test user login with email/password
- [ ] **JWT**: Test token generation and refresh
- [ ] **Password Reset**: Test password reset flow
- [ ] **Permissions**: Test permission checking in views
- [ ] **Module Access**: Test module access control
- [ ] **Activity Logging**: Verify activities are being tracked
- [ ] **User Sessions**: Check session tracking
- [ ] **RBAC**: Test role assignment and permission queries
- [ ] **Admin Panel**: Verify Django admin works

### 3. API Testing

```bash
# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Test protected endpoint
curl http://localhost:8000/api/v1/activities/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Performance Testing

Monitor after migration:
- [ ] API response times (should be same or better)
- [ ] Database query count (should be same)
- [ ] Memory usage
- [ ] Activity logging overhead

## Rollback Plan

If issues occur during migration:

### Quick Rollback

```bash
# 1. Revert code changes
git reset --hard HEAD~1

# 2. Restore database from backup
# PostgreSQL
pg_restore -d your_database backup.dump

# MySQL
mysql your_database < backup.sql

# 3. Restart services
systemctl restart gunicorn
systemctl restart celery
```

### Partial Rollback

If only some modules have issues:

```python
# settings.py - Keep old and new side by side temporarily

INSTALLED_APPS = [
    # Old (keep temporarily)
    'apps.authentication',
    'apps.rbac',
    
    # New (testing)
    'user_management.authentication',
    'user_management.authorization',
]

# Use feature flags to switch between old/new code
USE_NEW_USER_MANAGEMENT = os.getenv('USE_NEW_USER_MANAGEMENT', 'False') == 'True'
```

## Common Issues and Solutions

### Issue 1: Import Errors

**Error**: `ModuleNotFoundError: No module named 'apps.authentication'`

**Solution**: 
```bash
# Find all old imports
grep -r "from apps\." --include="*.py"

# Replace automatically
find . -name "*.py" -exec sed -i 's/from apps\./from user_management./g' {} +
```

### Issue 2: Migration Conflicts

**Error**: `Conflicting migrations detected`

**Solution**:
```bash
# Reset migrations
python manage.py migrate --fake user_management zero
python manage.py migrate user_management
```

### Issue 3: User Model Mismatch

**Error**: `AUTH_USER_MODEL is set to 'authentication.CustomUser', but no such model exists`

**Solution**:
```python
# settings.py
AUTH_USER_MODEL = 'authentication.User'  # Update to new model name
```

### Issue 4: Permission Denied

**Error**: Users can't access features they previously could

**Solution**:
```python
# Verify role assignments
from user_management.authorization.models import UserRole

# Check user's roles
user_roles = UserRole.objects.filter(user=user)
for ur in user_roles:
    print(f"Role: {ur.role.name}, Primary: {ur.is_primary}")

# Reassign if needed
```

## Post-Migration Tasks

After successful migration:

1. **Update Documentation**: Update internal docs with new import paths
2. **Train Team**: Brief team on new package structure
3. **Monitor Logs**: Watch for errors in first 24-48 hours
4. **Remove Old Code**: After 1-2 weeks of stability, remove old apps
5. **Cleanup**: Remove old migration files and unused imports

## Support

If you need help during migration:

- Check [ARCHITECTURE.md](ARCHITECTURE.md) for module structure
- Review [USAGE.md](USAGE.md) for code examples
- Check test files for usage patterns
- Review commit history for context

## Migration Checklist

Final checklist before declaring migration complete:

- [ ] All imports updated
- [ ] Database migrated successfully
- [ ] All tests passing
- [ ] Manual testing complete
- [ ] API tests passing
- [ ] Performance metrics acceptable
- [ ] No errors in logs
- [ ] Team briefed on changes
- [ ] Documentation updated
- [ ] Backup verified and stored safely
- [ ] Monitoring alerts configured
- [ ] Rollback plan tested (in staging)

**Migration Complete!** 🎉
