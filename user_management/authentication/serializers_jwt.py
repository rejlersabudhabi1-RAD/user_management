"""
Custom JWT serializers for email-based authentication.

IMPORTANT: Maintains backward compatibility with existing authentication flow.
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger(__name__)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that accepts email instead of username.
    
    This serializer replaces the default username-based authentication
    with email-based authentication while maintaining full JWT compatibility.
    
    Features:
    - Email field instead of username
    - Proper error handling and logging
    - Active user validation
    - Standard JWT token generation
    """
    username_field = 'email'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace username field with email field
        self.fields['email'] = serializers.EmailField(
            required=True,
            help_text="User's email address"
        )
        # Remove username field if it exists
        self.fields.pop('username', None)
    
    def validate(self, attrs):
        """
        Validate credentials and generate JWT tokens.
        
        Process:
        1. Extract email and password
        2. Authenticate user with Django's authenticate()
        3. Validate user is active
        4. Generate refresh and access tokens
        
        Args:
            attrs: Request data with email and password
            
        Returns:
            dict: JWT tokens (refresh and access)
            
        Raises:
            ValidationError: If authentication fails
        """
        # Get email and password from request
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Authenticate using email
            # Note: Django's authenticate expects 'username' parameter
            try:
                user = authenticate(
                    request=self.context.get('request'),
                    username=email,  # Pass email as username
                    password=password
                )
            except Exception as e:
                logger.exception(f"Authentication error for {email}: {e}")
                raise serializers.ValidationError(
                    'Authentication failed. Please try again.',
                    code='authorization'
                )
            
            # Check if user exists
            if not user:
                raise serializers.ValidationError(
                    'No active account found with the given credentials',
                    code='authorization'
                )
            
            # Check if user is active
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled',
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password"',
                code='authorization'
            )
        
        # Generate tokens using the parent class method
        refresh = self.get_token(user)
        
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        return data
