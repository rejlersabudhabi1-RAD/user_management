"""
Tests for Authorization Module.

Comprehensive test coverage for RBAC functionality.
"""
import pytest
from django.contrib.auth import get_user_model

from user_management.authorization.models import (
    Organization, Module, Permission, Role, RolePermission, 
    RoleModule, UserProfile, UserRole
)

User = get_user_model()


@pytest.mark.django_db
class TestOrganization:
    """Test cases for Organization model"""
    
    def test_create_organization(self):
        """Test creating an organization"""
        org = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG',
            description='Test description'
        )
        
        assert org.name == 'Test Organization'
        assert org.code == 'TEST_ORG'
        assert org.is_active
    
    def test_organization_str(self):
        """Test organization string representation"""
        org = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG'
        )
        
        assert str(org) == 'Test Organization (TEST_ORG)'


@pytest.mark.django_db
class TestModule:
    """Test cases for Module model"""
    
    def test_create_module(self):
        """Test creating a module"""
        module = Module.objects.create(
            name='PID Analysis',
            code='PID',
            description='P&ID verification module'
        )
        
        assert module.name == 'PID Analysis'
        assert module.code == 'PID'
        assert module.is_active
    
    def test_module_ordering(self):
        """Test module ordering"""
        Module.objects.create(name='Module C', code='C', order=3)
        Module.objects.create(name='Module A', code='A', order=1)
        Module.objects.create(name='Module B', code='B', order=2)
        
        modules = list(Module.objects.all())
        assert modules[0].code == 'A'
        assert modules[1].code == 'B'
        assert modules[2].code == 'C'


@pytest.mark.django_db
class TestPermission:
    """Test cases for Permission model"""
    
    def test_create_permission(self):
        """Test creating a permission"""
        module = Module.objects.create(name='PID Analysis', code='PID')
        
        permission = Permission.objects.create(
            module=module,
            name='Create PID',
            code='pid.create',
            action='create',
            description='Permission to create PID documents'
        )
        
        assert permission.module == module
        assert permission.code == 'pid.create'
        assert permission.action == 'create'
    
    def test_permission_resource_type(self):
        """Test permission with resource type"""
        module = Module.objects.create(name='PID Analysis', code='PID')
        
        permission = Permission.objects.create(
            module=module,
            name='View PID',
            code='pid.view',
            action='read',
            resource_type='document'
        )
        
        assert permission.resource_type == 'document'


@pytest.mark.django_db
class TestRole:
    """Test cases for Role model"""
    
    def test_create_role(self):
        """Test creating a role"""
        role = Role.objects.create(
            name='Admin',
            code='admin',
            level=2,
            description='Administrator role'
        )
        
        assert role.name == 'Admin'
        assert role.code == 'admin'
        assert role.level == 2
        assert role.is_active
    
    def test_role_hierarchy(self):
        """Test role hierarchy levels"""
        super_admin = Role.objects.create(name='Super Admin', code='super_admin', level=1)
        admin = Role.objects.create(name='Admin', code='admin', level=2)
        manager = Role.objects.create(name='Manager', code='manager', level=3)
        
        assert super_admin.level < admin.level
        assert admin.level < manager.level


@pytest.mark.django_db
class TestRBACUserProfile:
    """Test cases for RBAC UserProfile model"""
    
    def test_create_user_profile(self):
        """Test creating a user profile with RBAC"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        org = Organization.objects.create(name='Test Org', code='TEST')
        
        profile = UserProfile.objects.create(
            user=user,
            organization=org,
            status='active'
        )
        
        assert profile.user == user
        assert profile.organization == org
        assert profile.status == 'active'
    
    def test_has_permission(self):
        """Test permission checking"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        org = Organization.objects.create(name='Test Org', code='TEST')
        profile = UserProfile.objects.create(user=user, organization=org)
        
        # Create role with permission
        role = Role.objects.create(name='Admin', code='admin', level=2)
        module = Module.objects.create(name='PID', code='PID')
        permission = Permission.objects.create(
            module=module,
            name='View PID',
            code='pid.view',
            action='read'
        )
        
        # Assign permission to role
        RolePermission.objects.create(role=role, permission=permission)
        
        # Assign role to user
        UserRole.objects.create(user=user, role=role, is_primary=True)
        
        # Check permission
        assert profile.has_permission('pid.view')
    
    def test_has_module_access(self):
        """Test module access checking"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        org = Organization.objects.create(name='Test Org', code='TEST')
        profile = UserProfile.objects.create(user=user, organization=org)
        
        # Create role with module
        role = Role.objects.create(name='User', code='user', level=4)
        module = Module.objects.create(name='PID', code='PID')
        
        # Assign module to role
        RoleModule.objects.create(role=role, module=module)
        
        # Assign role to user
        UserRole.objects.create(user=user, role=role, is_primary=True)
        
        # Check module access
        assert profile.has_module_access('PID')


@pytest.mark.django_db
class TestPermissions:
    """Test cases for permission classes"""
    
    def test_super_admin_has_all_permissions(self):
        """Test that super admin has all permissions"""
        user = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='testpass123'
        )
        
        org = Organization.objects.create(name='Test Org', code='TEST')
        profile = UserProfile.objects.create(user=user, organization=org)
        
        # Create super admin role
        super_admin_role = Role.objects.create(
            name='Super Admin',
            code='super_admin',
            level=1
        )
        
        # Assign role
        UserRole.objects.create(user=user, role=super_admin_role, is_primary=True)
        
        # Super admin should have access to any permission
        assert profile.has_permission('any.permission')
        assert profile.has_module_access('ANY_MODULE')
