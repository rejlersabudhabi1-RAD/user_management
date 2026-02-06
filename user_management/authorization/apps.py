"""
Django app configuration for Authorization module
"""
from django.apps import AppConfig


class AuthorizationConfig(AppConfig):
    """Configuration for the authorization app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_management.authorization'
    label = 'authorization'
    verbose_name = 'Authorization & RBAC'
    
    def ready(self):
        """
        Import signal handlers when app is ready
        """
        # Import signals here if needed
        pass
