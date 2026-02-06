"""
User models for authentication and profile management.

IMPORTANT: This is extracted from the main application.
DO NOT modify the core logic - maintain backward compatibility.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from user_management.core.models import TimeStampedModel


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    
    Key Features:
    - Email-based authentication (email is unique)
    - First login tracking with password change requirement
    - Password expiry and reset tracking
    - Email verification
    
    CRITICAL: This model is used across multiple applications.
    Do NOT modify fields without migration plan.
    """
    email = models.EmailField(
        unique=True,
        help_text="User's email address - used for login"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Contact phone number"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Profile avatar image"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="User biography/description"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Email verification status"
    )
    
    # First-time login and password reset tracking
    is_first_login = models.BooleanField(
        default=True,
        help_text='True if user has not logged in yet'
    )
    must_reset_password = models.BooleanField(
        default=False,
        help_text='True if user must reset password'
    )
    temp_password_created_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When temporary password was set'
    )
    last_password_change = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time password was changed'
    )
    
    # Email-based authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email


class UserProfile(TimeStampedModel):
    """
    Extended user profile information.
    
    Provides additional user details beyond authentication data.
    Linked 1:1 with User model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="Link to User account"
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="User's date of birth"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Street address"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="City"
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Country"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Postal/ZIP code"
    )

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.email}"
