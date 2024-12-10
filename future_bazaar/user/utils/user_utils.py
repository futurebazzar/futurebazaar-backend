from ..serializers import UserSignupSerializer
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from typing import Optional
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError
from ..models import UserModel




def hash_password(password: str) -> str:
    """Hash the user's password securely."""
    return make_password(password)

def user_sign_up(request: Request) -> Optional[Response]:
    """Handles user signup logic."""

    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        # Ensure transaction consistency in case of database operations
        with transaction.atomic():
           
            serializer.validated_data['password'] = make_password(serializer.validated_data['password'])
            serializer.user_type= 'end_user' # Set the default user type as 'end_user'
            user = serializer.save()    
                
        return Response({
                        'message': 'User created successfully',
                        'user': {
                            'user_id': user.user_id,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'contact_number': user.contact_number,

                        }
                    }, status=status.HTTP_201_CREATED)
    
    
    else:
        raise ValidationError(serializer.errors)
    


def authenticate_user(identifier: str, password: str) -> dict:

    if not identifier or not password:
        raise AuthenticationFailed("Identifier (email/contact_number) and password are required.")

    try:
        # Find the user by email or contact_number
        user = (
            UserModel.objects.get(email=identifier)
            if '@' in identifier
            else UserModel.objects.get(contact_number=identifier)
        )
    except UserModel.DoesNotExist:
        raise AuthenticationFailed("Invalid credentials.")

    # Verify password
    if not user.check_password(password):
        raise AuthenticationFailed("Invalid credentials.")

    if not user.is_active:
        raise AuthenticationFailed("User account is inactive.")

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "user_id": user.user_id,
        "email": user.email,
        "contact_number": user.contact_number,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "user_type": user.user_type,
    }



def deactivate_account(user: UserModel) -> None:
    """
    Helper function to deactivate a user's account.
    Args:
        user (UserModel): The user whose account needs to be deactivated.
    """
    if not user.is_active:
        raise ValidationError("User account is already deactivated.")
    user.is_active = False
    user.save()