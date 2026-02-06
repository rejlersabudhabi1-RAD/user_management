"""
Serializers for user authentication and profile management.

IMPORTANT: Extracted from main application - maintain backward compatibility.
Do NOT modify core logic without migration plan.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    
    Handles extended user data beyond authentication.
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'date_of_birth', 
            'address', 
            'city', 
            'country', 
            'postal_code'
        ]
        extra_kwargs = {
            'date_of_birth': {'required': False},
            'address': {'required': False},
            'city': {'required': False},
            'country': {'required': False},
            'postal_code': {'required': False},
        }


class UserSerializer(serializers.ModelSerializer):
    """
    Main user serializer with profile and role information.
    
    Includes:
    - Basic user info (email, name, phone, etc.)
    - Nested profile data
    - User roles (fetched from RBAC module if available)
    """
    profile = UserProfileSerializer(read_only=True)
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'phone_number', 
            'avatar', 
            'bio', 
            'is_verified', 
            'is_staff', 
            'is_superuser', 
            'profile', 
            'roles'
        ]
        read_only_fields = ['id', 'is_verified', 'is_staff', 'is_superuser']
    
    def get_roles(self, obj):
        """
        Get user's RBAC roles from authorization module.
        
        This method safely handles the case where RBAC module
        might not be installed or configured.
        
        Returns:
            list: User roles with id, code, name, and level
        """
        try:
            # Dynamic import to avoid hard dependency on authorization module
            from user_management.authorization.models import UserProfile as RBACUserProfile
            
            rbac_profile = RBACUserProfile.objects.filter(
                user=obj, 
                is_deleted=False
            ).first()
            
            if rbac_profile:
                roles = rbac_profile.roles.all()
                return [
                    {
                        'id': str(role.id), 
                        'code': role.code, 
                        'name': role.name, 
                        'level': role.level
                    } 
                    for role in roles
                ]
        except (ImportError, Exception) as e:
            # Soft failure - log but don't break serialization
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Could not fetch roles for user {obj.id}: {str(e)}")
        
        return []


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for new user registration.
    
    Handles:
    - Password confirmation validation
    - Secure password hashing
    - Automatic profile creation
    """
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters"
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        min_length=8,
        style={'input_type': 'password'},
        help_text="Re-enter password for confirmation"
    )
    
    class Meta:
        model = User
        fields = [
            'username', 
            'email', 
            'password', 
            'password_confirm', 
            'first_name', 
            'last_name'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_email(self, value):
        """
        Validate email uniqueness.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()
    
    def validate(self, attrs):
        """
        Validate password confirmation matches.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })
        return attrs
    
    def create(self, validated_data):
        """
        Create new user with hashed password and profile.
        
        Process:
        1. Remove password_confirm (not needed for creation)
        2. Extract password
        3. Create user using Django's create_user (handles hashing)
        4. Create associated UserProfile
        5. Return created user
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Create user with hashed password
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create associated profile
        UserProfile.objects.create(user=user)
        
        return user
