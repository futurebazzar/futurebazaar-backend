from ..serializers import UserSignupSerializer, UserUpdateSerializer, SellerSerializer
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from typing import Optional
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError
from ..models import UserModel, BlacklistedAccessToken
from rest_framework.exceptions import NotFound, ValidationError
from typing import Union




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
                
            return {
                        'message': 'User created successfully',
                        'user': {
                            'user_id': user.user_id,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'contact_number': user.contact_number,

                        }}
    
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
        raise AuthenticationFailed("Your account is deactive.")

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


def update_user_details(user: UserModel, data: dict) -> Response:
    """Helper function to update user details including password."""
    serializer = UserUpdateSerializer(user, data=data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "User updated successfully.",
            "user": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "contact_number": user.contact_number
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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


def deactivate_user_account(user: UserModel, user_id: Union[int, None] = None) -> Response:
    """Helper function to deactivate a user account."""
    if user.user_type == "admin":  # Admin can deactivate any user
        if not user_id:
            raise ValidationError("User ID is required to deactivate another user's account.")
        try:
            target_user = UserModel.objects.get(user_id=user_id)
        except UserModel.DoesNotExist:
            raise NotFound("User not found.")


        deactivate_account(target_user)

        return Response({
            "message": f"User with ID {user_id} has been deactivated successfully."
        }, status=status.HTTP_200_OK)
    
    else:
        # Non-admin users can deactivate only their own accounts
        deactivate_account(user)

        return Response({
            "message": "Your account has been deactivated successfully."
        }, status=status.HTTP_200_OK)
    

def blacklist_tokens(refresh_token: str, access_token: str) -> Response:
    """
    Helper function to blacklist the refresh and access tokens.
    """
    try:
        # Blacklist refresh token
        token = RefreshToken(refresh_token)
        token.blacklist()

        # Blacklist access token
        BlacklistedAccessToken.objects.create(token=access_token)

        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': f"Token invalid or expired: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    


def create_seller_profile(user: UserModel, request_data: dict) -> Response:

    try:

        # Check if seller profile already exists
        if hasattr(user, "seller"):
            return Response(
                {"error": "Seller profile already exists for this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deserialize and validate data
        serializer = SellerSerializer(data=request_data)
        if serializer.is_valid():

            # Update user type to 'seller'
            user.user_type = "seller"
            user.save()

            # Save seller profile
            serializer.save(user_id=user, is_approved=False, is_active=False, is_seller_exclusives=False)

            return Response(
                {"message": "Seller profile created successfully. Pending admin approval."},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
