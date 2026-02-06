"""
RBAC Utility Functions.

Helper functions for permission checking, audit logging, and feature access.

IMPORTANT: Extracted from main application - maintain backward compatibility.
"""
from .models import AuditLog


def create_audit_log(user, action, resource_type, resource_id=None, resource_repr='',
                     changes=None, metadata=None, ip_address=None, user_agent='',
                     success=True, error_message=''):
    """
    Create an audit log entry.
    
    Args:
        user: User performing the action
        action: Action performed (create, update, delete, etc.)
        resource_type: Type of resource (model name)
        resource_id: ID of the resource (optional)
        resource_repr: String representation of resource
        changes: Dict of before/after values
        metadata: Additional context
        ip_address: Client IP address
        user_agent: Client user agent
        success: Whether action succeeded
        error_message: Error message if failed
        
    Returns:
        AuditLog: Created audit log entry
    """
    return AuditLog.objects.create(
        user=user,
        user_email=user.email if user else 'system',
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_repr=resource_repr,
        changes=changes or {},
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        error_message=error_message
    )


def get_user_permissions(user):
    """
    Get all permissions for a user.
    
    Args:
        user: User instance
        
    Returns:
        list: List of permission codes
    """
    try:
        profile = user.rbac_profile
        permissions = profile.get_all_permissions()
        return [p.code for p in permissions]
    except:
        return []


def get_user_modules(user):
    """
    Get all accessible modules for a user.
    
    Args:
        user: User instance
        
    Returns:
        list: List of module codes
    """
    try:
        profile = user.rbac_profile
        modules = profile.get_all_modules()
        return [m.code for m in modules]
    except:
        return []


def check_user_has_module_access(user, module_code):
    """
    Check if user has access to a specific module.
    
    Args:
        user: User instance
        module_code: Module code to check
        
    Returns:
        bool: True if user has access
    """
    if user.is_superuser:
        return True
    
    user_modules = get_user_modules(user)
    return module_code in user_modules


def get_user_accessible_features(user):
    """
    Get list of features/routes user has access to based on their modules.
    
    Args:
        user: User instance
        
    Returns:
        dict: Feature codes and their accessible status
    """
    user_modules = get_user_modules(user)
    
    # Map modules to frontend feature routes
    # This can be customized based on your application's modules
    feature_map = {
        'PID': {
            'code': 'PID',
            'name': 'P&ID Design Verification',
            'route': '/pid/upload',
            'accessible': 'PID' in user_modules
        },
        'PFD': {
            'code': 'PFD',
            'name': 'PFD to P&ID Converter',
            'route': '/pfd/upload',
            'accessible': 'PFD' in user_modules
        },
        'CRS': {
            'code': 'CRS',
            'name': 'CRS Document Management',
            'route': '/crs/documents',
            'accessible': 'CRS' in user_modules
        },
        'PROJECT_CONTROL': {
            'code': 'PROJECT_CONTROL',
            'name': 'Project Control',
            'route': '/projects',
            'accessible': 'PROJECT_CONTROL' in user_modules
        }
    }
    
    return feature_map
