"""
Django app configuration for Activity module
"""
from django.apps import AppConfig


class ActivityConfig(AppConfig):
    """Configuration for the activity app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_management.activity'
    label = 'activity'
    verbose_name = 'Activity Tracking'
    
    def ready(self):
        """
        Import signal handlers when app is ready
        """
        # Import signals here if needed
        pass
