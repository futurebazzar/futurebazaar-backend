# Standard Library
import logging

# Django Modules
from django.db import IntegrityError

# DRF Modules
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated

# DRF Extensions
from drf_yasg.utils import swagger_auto_schema

# Local Modules
from .models import UserModel
from .serializers import UserSignupSerializer, UserLoginRequestSerializer, UserUpdateSerializer
from .utils.user_utils import user_sign_up, authenticate_user

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