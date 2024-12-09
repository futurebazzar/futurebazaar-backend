from rest_framework import serializers
from .models import UserModel
from django.contrib.auth.hashers import make_password

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name', 'email',  'profile_photo','contact_number', 'password']
        extra_kwargs = {
            'password': {'write_only': True},  # Ensure password is write-only
        }

    def validate_first_name(self, value: str) -> str:
        """Ensure the first name contains only valid characters."""
        if not value.isalpha():
            raise serializers.ValidationError("First name must contain only alphabetic characters.")
        return value

    def validate_last_name(self, value: str) -> str:
        """Ensure the last name contains only valid characters."""
        if not value.isalpha():
            raise serializers.ValidationError("Last name must contain only alphabetic characters.")
        return value

    def validate_email(self, value: str) -> str:
        """Ensure the email is unique."""
        if UserModel.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_contact_number(self, value: str) -> str:
        """Ensure contact number meets the required format."""
        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError("Contact number must be between 10 and 15 digits.")
        if UserModel.objects.filter(contact_number=value).exists():
            raise serializers.ValidationError("A user with this contact number already exists.")
        
        return value



    def create(self, validated_data: dict) -> UserModel:
        """Handle user creation, including password hashing and setting default user_type."""
        user = UserModel(**validated_data)
        user.save()
        return user
    

class UserLoginRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True, help_text="The username or email of the user.")
    password = serializers.CharField(required=True, write_only=True, help_text="The password of the user.")
    
    
class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name', 'email', 'contact_number', 'password']

    def validate_password(self, value):
        """Validate and hash the password."""
        if value:
            return make_password(value)
        return value

    def update(self, instance, validated_data):
        """Update user details, including password and email."""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.password = password  # Already hashed
        instance.save()
        return instance
    
UserType = {
     
        'admin': 'Admin',
        'seller': 'Seller',
        'end_user': 'End User',
    
}
