# User Management System

A comprehensive, production-ready User Management system for Django applications with authentication, authorization, role-based access control (RBAC), and activity tracking.

## 🎯 Overview

This package provides a complete user management solution that can be integrated into any Django application. It handles:

- **Authentication**: JWT-based authentication with email login, password management, and email verification
- **Authorization**: Role-Based Access Control (RBAC) with permissions, modules, and subscriptions
- **Activity Tracking**: User sessions, audit logs, and system activity monitoring

## 🏗️ Architecture

```
user_management/
├── authentication/     # User authentication & password management
│   ├── models.py      # User, UserProfile
│   ├── services.py    # Email, password reset services
│   ├── serializers.py # User serializers & JWT
│   └── views.py       # Auth endpoints
│
├── authorization/     # RBAC & permissions
│   ├── models.py      # Role, Permission, UserRole
│   ├── middleware.py  # RBAC & feature access middleware
│   ├── permissions.py # Custom permission classes
│   └── views.py       # RBAC management endpoints
│
├── activity/          # Audit & session tracking
│   ├── models.py      # UserSession, ActivityLog
│   └── views.py       # Activity endpoints
│
├── core/              # Shared utilities
│   ├── models.py      # Base models (TimeStampedModel)
│   └── utils.py       # Common utilities
│
└── api/               # API gateway & routing
    ├── urls.py        # URL configuration
    └── views.py       # Main API views
```

## 📦 Installation

### From Source
```bash
git clone https://github.com/rejlersabudhabi1-RAD/user_management.git
cd user_management
pip install -e .
```

### From PyPI (when published)
```bash
pip install rad-user-management
```

## 🚀 Quick Start

### 1. Add to Django Settings

```python
# settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # User Management
    'user_management.authentication',
    'user_management.authorization',
    'user_management.activity',
]

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### 2. Include URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('user_management.authentication.urls')),
    path('api/rbac/', include('user_management.authorization.urls')),
    path('api/activity/', include('user_management.activity.urls')),
]
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 🔐 API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login/` | POST | Login with email & password |
| `/api/auth/refresh/` | POST | Refresh JWT token |
| `/api/auth/register/` | POST | Register new user |
| `/api/auth/verify-email/` | POST | Verify email address |
| `/api/auth/change-password/` | POST | Change password |
| `/api/auth/reset-password/` | POST | Request password reset |

### Authorization

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rbac/roles/` | GET, POST | Manage roles |
| `/api/rbac/permissions/` | GET, POST | Manage permissions |
| `/api/rbac/users/` | GET | List users with roles |
| `/api/rbac/users/{id}/assign-role/` | POST | Assign role to user |

### Activity

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/activity/sessions/` | GET | User sessions |
| `/api/activity/logs/` | GET | Audit logs |
| `/api/activity/timeline/` | GET | User activity timeline |

## 🔧 Configuration

### Environment Variables

```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_EXPIRY_DAYS=90
PASSWORD_HISTORY_COUNT=5

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=3600  # seconds
JWT_REFRESH_TOKEN_LIFETIME=604800  # seconds
```

## 🛡️ Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Policy**: Configurable password strength & expiry
- **Email Verification**: Email verification before activation
- **Role-Based Access**: Fine-grained permission control
- **Audit Logging**: Track all user activities
- **Session Management**: Monitor and control user sessions

## 📊 Features

### Authentication Module
- [x] Email-based login
- [x] JWT token management
- [x] Password reset flow
- [x] First login password change
- [x] Password expiry tracking
- [x] Email verification

### Authorization Module
- [x] Role management
- [x] Permission management
- [x] Module-based access control
- [x] Data visibility rules
- [x] Subscription management
- [x] Feature access middleware

### Activity Module
- [x] User session tracking
- [x] Audit log system
- [x] Activity timeline
- [x] System metrics
- [x] Security alerts

## 🔄 Backward Compatibility

This package is designed to be drop-in compatible with existing Django applications. All existing APIs, models, and authentication flows are preserved.

### Migration from Existing System

If you're migrating from an existing user management system:

1. **Backup your database**
2. Run migrations with `--fake-initial` if needed
3. Test authentication flows thoroughly
4. Verify role/permission mappings

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/authentication/
pytest tests/authorization/
pytest tests/activity/

# With coverage
pytest --cov=user_management
```

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Migration Guide](docs/MIGRATION.md)
- [Security Best Practices](docs/SECURITY.md)

## 🤝 Contributing

This is an internal project. For contributions or issues, contact the development team.

## 📝 License

Proprietary - Rejlers Abu Dhabi

## 🔗 Links

- **GitHub**: https://github.com/rejlersabudhabi1-RAD/user_management
- **Main Application**: https://github.com/rejlersabudhabi1-RAD/aiflow_backend

## 📞 Support

For issues or questions:
- Create an issue in GitHub
- Contact: development@rejlers.ae

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Maintained by**: Rejlers Abu Dhabi - RAD Team
