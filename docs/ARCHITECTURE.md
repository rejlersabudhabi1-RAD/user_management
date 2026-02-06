# User Management System - Architecture Documentation

## 🏗️ System Overview

The User Management System is a modular, scalable Django package that provides complete user lifecycle management, authentication, authorization, and activity tracking capabilities.

## 📐 Architecture Principles

1. **Separation of Concerns**: Clear boundaries between authentication, authorization, and activity tracking
2. **Backward Compatibility**: All changes must maintain existing API contracts
3. **Modularity**: Each module can function independently
4. **Reusability**: Designed to be consumed by multiple applications
5. **Security First**: Built-in security best practices and audit trail

## 🔧 Core Components

### 1. Authentication Module (`authentication/`)

**Purpose**: Handle user identity, credentials, and authentication mechanisms

**Components**:
- **Models**:
  - `User` (extends Django's AbstractUser) - Core user model with email-based login
  - `UserProfile` - Extended user information and settings

- **Services**:
  - `EmailService` - Email sending and templating
  - `PasswordResetService` - Secure password reset flow with tokens
  - `EmailValidationService` - Email validation and verification

- **Serializers**:
  - `UserSerializer` - User data serialization
  - `UserRegistrationSerializer` - New user registration
  - `EmailTokenObtainPairSerializer` - Custom JWT with email login

- **Views/Endpoints**:
  - `/auth/login/` - JWT token authentication
  - `/auth/refresh/` - Token refresh
  - `/auth/register/` - User registration
  - `/auth/verify-email/` - Email verification
  - `/auth/change-password/` - Password change
  - `/auth/reset-password/` - Password reset flow
  - `/auth/check-first-login/` - First login check
  - `/auth/check-password-expiry/` - Password expiry check

**Key Features**:
- Email-based authentication (no username required)
- JWT token management with refresh
- Password policy enforcement (length, expiry, history)
- Email verification workflow
- First login password change requirement
- Password reset via email tokens

### 2. Authorization Module (`authorization/`)

**Purpose**: Manage roles, permissions, and access control

**Components**:
- **Models**:
  - `Organization` - Multi-tenancy support
  - `Module` - System modules/features
  - `Permission` - Granular permissions
  - `Role` - User roles with permissions
  - `RolePermission` - Role-permission mapping
  - `RoleModule` - Role-module access
  - `UserRole` - User-role assignment
  - `UserStorage` - User storage quotas

- **Middleware**:
  - `RBACMiddleware` - Role-based access control enforcement
  - `FeatureAccessMiddleware` - Module-level feature gating

- **Permissions**:
  - Custom DRF permission classes
  - Data visibility rules
  - Team collaboration permissions

- **Views/Endpoints**:
  - `/rbac/organizations/` - Organization management
  - `/rbac/modules/` - Module management
  - `/rbac/permissions/` - Permission management
  - `/rbac/roles/` - Role CRUD operations
  - `/rbac/users/` - User-role management
  - `/rbac/users/{id}/assign-role/` - Role assignment
  - `/rbac/dashboard/stats/` - User dashboard statistics

**Key Features**:
- Multi-tenant organization support
- Hierarchical role system
- Granular permission control
- Module-based feature access
- Data visibility rules (own/team/organization/all)
- Subscription and quota management
- Audit logging for all changes

### 3. Activity Module (`activity/`)

**Purpose**: Track user actions, sessions, and system events

**Components**:
- **Models**:
  - `UserSession` - Active user sessions
  - `SystemActivity` - System-wide activity log
  - `ActivityStream` - User activity timeline
  - `AuditLog` - Audit trail for security

- **Views/Endpoints**:
  - `/activity/sessions/` - User session management
  - `/activity/logs/` - Audit log access
  - `/activity/timeline/` - User activity timeline
  - `/activity/statistics/` - Activity statistics

**Key Features**:
- Session tracking with IP and device info
- Real-time activity stream
- Comprehensive audit logging
- Security event monitoring
- Activity analytics and reporting

### 4. Core Module (`core/`)

**Purpose**: Shared utilities, base models, and common functionality

**Components**:
- **Base Models**:
  - `TimeStampedModel` - Auto-created/updated timestamps
  - `SoftDeleteModel` - Soft deletion support

- **Utilities**:
  - Date/time helpers
  - Validation utilities
  - Common decorators
  - Logging helpers

### 5. API Gateway (`api/`)

**Purpose**: Centralized API routing and version management

**Components**:
- URL routing configuration
- API versioning
- Common API views
- Health check endpoints

## 🔄 Data Flow

### Authentication Flow
```
User → Login Request → EmailTokenObtainPairView
                      ↓
                  Validate Credentials
                      ↓
                  Check Email Verified
                      ↓
                  Check First Login
                      ↓
                  Generate JWT Tokens
                      ↓
                  Return Access + Refresh Token
```

### Authorization Flow
```
Request → JWT Authentication → User Identified
                              ↓
                        RBACMiddleware
                              ↓
                        Check User Roles
                              ↓
                        Check Permissions
                              ↓
                        Check Module Access
                              ↓
                        Apply Data Visibility
                              ↓
                        Allow/Deny Request
```

### Activity Logging Flow
```
User Action → Create ActivityLog Entry
                    ↓
              Update UserSession
                    ↓
              Check Security Alerts
                    ↓
              Store in Database
                    ↓
              Emit Real-time Event
```

## 🗄️ Database Schema

### Core Tables

**users (authentication_user)**
- id (PK)
- email (unique)
- password (hashed)
- first_name, last_name
- is_active, is_staff, is_superuser
- email_verified
- require_password_change
- password_changed_at
- created_at, updated_at

**user_profiles (authentication_userprofile)**
- id (PK)
- user_id (FK → User)
- phone_number
- avatar
- organization_id (FK → Organization)
- storage_used, storage_limit
- created_at, updated_at

**roles (authorization_role)**
- id (PK)
- name, description
- organization_id (FK → Organization)
- is_system_role
- created_at, updated_at

**permissions (authorization_permission)**
- id (PK)
- name, codename, description
- module_id (FK → Module)
- created_at, updated_at

**user_roles (authorization_userrole)**
- id (PK)
- user_id (FK → User)
- role_id (FK → Role)
- assigned_by_id (FK → User)
- assigned_at

## 🔐 Security Architecture

### Authentication Security
- Passwords hashed with Django's PBKDF2 algorithm
- JWT tokens with configurable expiry
- Refresh token rotation
- Email verification before activation
- Password policy enforcement
- Password history tracking
- Account lockout after failed attempts

### Authorization Security
- Principle of least privilege
- Role-based access control (RBAC)
- Permission inheritance
- Data visibility enforcement
- Audit logging for all sensitive actions
- Session management and timeout

### API Security
- CORS configuration
- Rate limiting (configurable)
- HTTPS enforcement (production)
- CSRF protection
- SQL injection prevention (Django ORM)
- XSS protection

## 📊 Performance Considerations

### Database Optimization
- Indexed fields: email, username, role names
- Select_related for FK queries
- Prefetch_related for M2M relationships
- Database connection pooling
- Query result caching

### API Optimization
- Pagination for list endpoints
- Field filtering to reduce payload
- Conditional requests (ETag, Last-Modified)
- Response compression

## 🔌 Integration Points

### External Systems
- **Email Service**: SMTP or API-based (Mailgun, SendGrid)
- **Storage**: S3-compatible storage for avatars
- **Cache**: Redis for session and token caching
- **Logging**: Centralized logging system
- **Monitoring**: Application performance monitoring

### Internal Integration
- Signals for cross-module communication
- Event-driven architecture where applicable
- Middleware for request/response processing
- Custom DRF permissions for fine-grained control

## 🧪 Testing Strategy

### Unit Tests
- Model validation
- Serializer logic
- Service functions
- Utility functions

### Integration Tests
- API endpoint testing
- Authentication flow
- Authorization checks
- Database transactions

### Security Tests
- Permission bypass attempts
- SQL injection tests
- XSS vulnerability tests
- CSRF protection
- Rate limiting

## 📈 Scalability

### Horizontal Scaling
- Stateless API design
- JWT tokens (no server-side sessions)
- Database read replicas
- Load balancer ready

### Vertical Scaling
- Optimized queries
- Connection pooling
- Async task processing (Celery)
- Caching layer

## 🔄 Future Enhancements

### Planned Features
- [ ] Two-factor authentication (2FA)
- [ ] OAuth2/SAML integration
- [ ] Advanced audit reporting
- [ ] IP whitelisting/blacklisting
- [ ] Device management
- [ ] Role delegation/impersonation
- [ ] GraphQL API
- [ ] WebSocket support for real-time updates

## 📝 Configuration Options

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration options.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

**Document Version**: 1.0.0  
**Last Updated**: February 2026  
**Maintained by**: Rejlers Abu Dhabi - RAD Team
