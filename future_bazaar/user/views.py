# Standard Library
import logging

# Django Modules
from django.db import IntegrityError
from typing import Union

# DRF Modules
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

# DRF Extensions
from drf_yasg.utils import swagger_auto_schema

# Local Modules
from .models import UserModel, BlacklistedAccessToken
from .serializers import UserSignupSerializer, UserLoginRequestSerializer, UserUpdateSerializer, LogoutSerializer
from .utils.user_utils import user_sign_up, authenticate_user, deactivate_account

# Set up logging for exception handling
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_api(request):
    return Response({"message": "This endpoint is public"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def private_api(request):
    return Response({"message": "This endpoint is private"})


@permission_classes([AllowAny])
@swagger_auto_schema(
    method='post',
    request_body=UserSignupSerializer,
    responses={201: "User Created", 400: "Invalid Input", 500: "Internal Server Error"}
)
@api_view(['POST'])
def user_signup(request: Request) -> Response:
    """Handles the POST request for user signup."""
    try:  
        user : UserModel = user_sign_up(request)
        return user
    
    except IntegrityError as e:
        logger.error(f"Database integrity error occurred: {e}")
        return Response({'error': 'Integrity error occurred, possibly a duplicate email.'},
                        status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        # Catching validation errors raised by the serializer (e.g., unique constraint failures)
        logger.error(f"Validation error occurred: {e}")    
        # Extracting and formatting the validation error details
        error_details = {field: [str(err) for err in errors] for field, errors in e.detail.items()}    
        return Response({'errors': error_details}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@swagger_auto_schema(
    method='post',
    request_body=UserLoginRequestSerializer,
    responses={
        200: "Login successful",
        401: "Unauthorized",
        400: "Bad Request"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request: Request) -> Response:
    """
    Handles user login using either email or contact_number and returns JWT tokens.
    """
    serializer = UserLoginRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    identifier = serializer.validated_data.get('identifier')
    password = serializer.validated_data.get('password')

    try:
        user_data = authenticate_user(identifier, password)
        return Response({
            "message": "Login successful",
            **user_data
        }, status=status.HTTP_200_OK)
    except AuthenticationFailed as e:
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        logging.error(f"Unexpected error in login: {str(e)}")
        return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@swagger_auto_schema(
    method='put',
    request_body=UserUpdateSerializer,
    responses={200: 'Updated successfully', 400: 'Bad Request'}
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request: Request) -> Response:
    """Update user details, including email and password."""
    user = request.user  # Authenticated user
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)

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


@swagger_auto_schema(
    method='patch',
    responses={
        200: "Account deactivated successfully",
        400: "Bad Request",
        404: "User not found",
        403: "Forbidden",
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def deactivate_user(request) -> Response:
    """
    Deactivates the user account. Only the authenticated user can deactivate their own account.
    Admins can deactivate any user account.
    """
    user: UserModel = request.user  # Get the authenticated user

    if user.user_type == "admin":  # Admin can deactivate any user
        user_id: Union[int, None] = request.data.get('user_id')
        if not user_id:
            raise ValidationError("User ID is required to deactivate another user's account.")
        try:
            target_user: UserModel = UserModel.objects.get(user_id=user_id)
        except UserModel.DoesNotExist:
            raise NotFound("User not found.")

        if target_user.user_type == "admin":
            raise PermissionDenied("Admin accounts cannot be deactivated by other admins.")
        
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
    

@swagger_auto_schema(
    method='post',
    request_body=LogoutSerializer,
    responses={
        200: "Logout successful",
        400: "Invalid request",
        500: "Server error",
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request) -> Response:
    """
    Blacklists the refresh token and access token.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        access_token = request.headers.get('Authorization', '')

        if not refresh_token:
            return Response({'error': 'Refresh token is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Blacklist refresh token
        token = RefreshToken(refresh_token)
        token.blacklist()

        # Blacklist access token
        BlacklistedAccessToken.objects.create(token=access_token)

        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Invalid or expired token.', 'details': str(e)},
                        status=status.HTTP_400_BAD_REQUEST)
    
