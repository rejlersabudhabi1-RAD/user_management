"""
Django app configuration for Core module
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_management.core'
    label = 'core'
    verbose_name = 'Core Utilities'
