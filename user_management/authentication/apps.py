"""
Django app configuration for Authentication module
"""
from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuration for the authentication app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_management.authentication'
    label = 'authentication'
    verbose_name = 'User Authentication'
    
    def ready(self):
        """
        Import signal handlers when app is ready
        """
        # Import signals here if needed
        pass
