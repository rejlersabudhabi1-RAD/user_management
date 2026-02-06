"""
RBAC Models - Enterprise Role-Based Access Control

Designed for multi-tenant organizations with hierarchical roles and granular permissions.

IMPORTANT: Extracted from main application - maintain backward compatibility.
Do NOT modify database schemas or relationships without migration plan.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from user_management.core.models import TimeStampedModel

User = get_user_model()


class Organization(TimeStampedModel):
    """
    Multi-tenant organization model.
    
    Each user belongs to one organization, enabling complete data isolation
    and organization-specific configuration (S3 buckets, branding, etc.).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Organization name"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique organization code"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Active organizations can access the system"
    )
    
    # Contact information
    primary_contact_name = models.CharField(max_length=255, blank=True)
    primary_contact_email = models.EmailField(blank=True)
    primary_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # S3 storage configuration
    s3_bucket_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Organization-specific S3 bucket"
    )
    s3_region = models.CharField(
        max_length=50,
        default='us-east-1',
        help_text="AWS region for S3 bucket"
    )
    
    class Meta:
        db_table = 'rbac_organizations'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class Module(TimeStampedModel):
    """
    Application modules/features that can be enabled/disabled per role.
    
    Examples: PID Analysis, QHSE Management, Procurement, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Module display name"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique module code for programmatic access"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Only active modules are available"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon name for UI display"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order in menus (lower first)"
    )
    
    class Meta:
        db_table = 'rbac_modules'
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class Permission(TimeStampedModel):
    """
    Granular permissions for actions within modules.
    
    Follows CRUD pattern plus domain-specific actions (approve, export, etc.).
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('execute', 'Execute'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text="Module this permission belongs to"
    )
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique permission code (e.g., 'pid_create')"
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable permission name"
    )
    description = models.TextField(blank=True)
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of action this permission allows"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active permissions are enforced"
    )
    
    class Meta:
        db_table = 'rbac_permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['module', 'action']
        unique_together = ['module', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['module', 'action']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.module.name}: {self.name}"


class Role(TimeStampedModel):
    """
    User roles with hierarchical structure.
    
    Roles determine:
    - Which modules users can access
    - Which permissions they have within those modules
    - Data visibility scope (own/team/org/all)
    """
    ROLE_LEVEL_CHOICES = [
        (1, 'Super Admin'),
        (2, 'Admin'),
        (3, 'Manager'),
        (4, 'Engineer'),
        (5, 'Reviewer'),
        (6, 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Role display name"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique role code"
    )
    description = models.TextField(blank=True)
    level = models.IntegerField(
        choices=ROLE_LEVEL_CHOICES,
        default=6,
        help_text="Hierarchical level (1=highest privilege, 6=lowest)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active roles can be assigned"
    )
    is_system_role = models.BooleanField(
        default=False,
        help_text="System roles cannot be deleted"
    )
    
    # Permissions
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        help_text="Permissions granted to this role"
    )
    
    # Module access
    modules = models.ManyToManyField(
        Module,
        through='RoleModule',
        related_name='roles',
        help_text="Modules accessible by this role"
    )
    
    class Meta:
        db_table = 'rbac_roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['level', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['level']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def has_permission(self, permission_code):
        """
        Check if role has specific permission.
        
        Args:
            permission_code: Permission code to check
            
        Returns:
            bool: True if role has the permission
        """
        return self.permissions.filter(code=permission_code, is_active=True).exists()
    
    def has_module_access(self, module_code):
        """
        Check if role has access to module.
        
        Args:
            module_code: Module code to check
            
        Returns:
            bool: True if role can access the module
        """
        return self.modules.filter(code=module_code, is_active=True).exists()


class RolePermission(TimeStampedModel):
    """
    Many-to-many relationship between roles and permissions.
    
    Tracks who granted specific permissions and when.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who granted this permission"
    )
    
    class Meta:
        db_table = 'rbac_role_permissions'
        unique_together = ['role', 'permission']
        indexes = [
            models.Index(fields=['role', 'permission']),
        ]
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class RoleModule(TimeStampedModel):
    """
    Many-to-many relationship between roles and modules.
    
    Tracks who granted module access and when.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who granted this module access"
    )
    
    class Meta:
        db_table = 'rbac_role_modules'
        unique_together = ['role', 'module']
        indexes = [
            models.Index(fields=['role', 'module']),
        ]
    
    def __str__(self):
        return f"{self.role.name} - {self.module.name}"


class UserProfile(TimeStampedModel):
    """
    Extended user profile with organization and RBAC.
    
    Central model for:
    - Organization membership
    - Role assignments
    - Login tracking
    - Profile customization
    - Password policy enforcement
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='rbac_profile',
        help_text="Link to User account"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='users',
        help_text="User's organization"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Account status"
    )
    is_mfa_enabled = models.BooleanField(
        default=False,
        help_text="Multi-factor authentication enabled"
    )
    
    # Roles
    roles = models.ManyToManyField(
        Role,
        through='UserRole',
        related_name='user_profiles',
        help_text="Assigned roles"
    )
    
    # Metadata
    employee_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible metadata storage (email tokens, preferences, etc.)"
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        help_text="Reporting manager"
    )
    
    # Login tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Password policy
    must_change_password = models.BooleanField(
        default=False,
        help_text="User must change password on next login"
    )
    
    # Profile customization
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        null=True,
        blank=True,
        help_text="User profile photo stored in S3"
    )
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True, max_length=500)
    location = models.CharField(max_length=100, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_profiles'
    )
    
    class Meta:
        db_table = 'rbac_user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['employee_id']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name}"
    
    def has_permission(self, permission_code):
        """
        Check if user has specific permission through any role.
        
        Args:
            permission_code: Permission code to check
            
        Returns:
            bool: True if user has the permission
        """
        user_role_ids = UserRole.objects.filter(user_profile=self).values_list('role_id', flat=True)
        return Permission.objects.filter(
            roles__id__in=user_role_ids,
            code=permission_code,
            is_active=True
        ).exists()
    
    def has_module_access(self, module_code):
        """
        Check if user has access to module through any role.
        
        Args:
            module_code: Module code to check
            
        Returns:
            bool: True if user can access the module
        """
        user_role_ids = UserRole.objects.filter(user_profile=self).values_list('role_id', flat=True)
        return Module.objects.filter(
            roles__id__in=user_role_ids,
            code=module_code,
            is_active=True
        ).exists()
    
    def get_all_permissions(self):
        """
        Get all permissions from all assigned roles.
        
        Returns:
            QuerySet: All unique permissions user has
        """
        return Permission.objects.filter(
            roles__in=self.roles.all(),
            is_active=True
        ).distinct()
    
    def get_all_modules(self):
        """
        Get all accessible modules from all assigned roles.
        
        Returns:
            QuerySet: All unique modules user can access
        """
        # Get role IDs through UserRole relationship
        user_role_ids = UserRole.objects.filter(user_profile=self).values_list('role_id', flat=True)
        
        # Get modules linked to these roles through RoleModule
        return Module.objects.filter(
            rolemodule__role_id__in=user_role_ids,
            is_active=True
        ).distinct()


class UserRole(TimeStampedModel):
    """
    Many-to-many relationship between users and roles.
    
    Tracks:
    - Which roles are assigned to which users
    - Who assigned the role
    - Whether it's the primary role (for display/default permissions)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        help_text="User this role is assigned to"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        help_text="Role being assigned"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who assigned this role"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary role used for default permissions"
    )
    
    class Meta:
        db_table = 'rbac_user_roles'
        unique_together = ['user_profile', 'role']
        indexes = [
            models.Index(fields=['user_profile', 'role']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.user_profile.user.email} - {self.role.name}"


class UserStorage(TimeStampedModel):
    """
    Track user file storage in S3.
    
    Maintains:
    - File metadata and checksums
    - S3 paths and buckets
    - Access tracking
    - Storage quotas
    """
    FILE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('drawing', 'P&ID Drawing'),
        ('report', 'Report'),
        ('model', 'AI Model'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='files',
        help_text="User who owns this file"
    )
    
    # File metadata
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_size = models.BigIntegerField(help_text="Size in bytes")
    mime_type = models.CharField(max_length=100)
    
    # S3 path
    s3_bucket = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=1024, help_text="Full S3 path")
    s3_region = models.CharField(max_length=50)
    
    # Checksum for integrity
    md5_checksum = models.CharField(max_length=32, blank=True)
    
    # Access tracking
    download_count = models.IntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'rbac_user_storage'
        verbose_name = 'User Storage'
        verbose_name_plural = 'User Storage'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_profile', 'file_type']),
            models.Index(fields=['s3_bucket', 's3_key']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.filename} - {self.user_profile.user.email}"
    
    @property
    def s3_path(self):
        """Full S3 path"""
        return f"s3://{self.s3_bucket}/{self.s3_key}"


class AuditLog(TimeStampedModel):
    """
    Comprehensive audit logging for compliance.
    
    Records all security-relevant actions:
    - Authentication events
    - Permission changes
    - Data modifications
    - File operations
    - Administrative actions
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('role_assign', 'Role Assign'),
        ('role_revoke', 'Role Revoke'),
        ('permission_grant', 'Permission Grant'),
        ('permission_revoke', 'Permission Revoke'),
        ('file_upload', 'File Upload'),
        ('file_download', 'File Download'),
        ('file_delete', 'File Delete'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
        ('mfa_enable', 'MFA Enable'),
        ('mfa_disable', 'MFA Disable'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    user_email = models.EmailField(help_text="Denormalized for historical record")
    
    # What
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=100, help_text="Model name")
    resource_id = models.UUIDField(null=True, blank=True)
    resource_repr = models.CharField(
        max_length=255,
        blank=True,
        help_text="String representation"
    )
    
    # When & Where
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Details
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Before/after values"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context"
    )
    
    # Result
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'rbac_audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user_email} - {self.action} - {self.timestamp}"
