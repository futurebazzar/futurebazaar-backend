# Standard Library
import logging

# Django Modules
from django.db import IntegrityError

# DRF Modules
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError, AuthenticationFailed, PermissionDenied, NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg import openapi

# DRF Extensions
from drf_yasg.utils import swagger_auto_schema

# Local Modules
from .models import UserModel
from .serializers import UserSerializer, UserLoginRequestSerializer,  LogoutSerializer, SellerSerializer, CustomPagination
from .utils.user_utils import user_sign_up, authenticate_user, deactivate_user_account, update_user_details, create_seller_profile, blacklist_tokens, get_seller_profile_and_update, get_nearby_sellers, delete_seller_helper, deactivate_seller_helper

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
    request_body=UserSerializer,
    responses={201: "User Created", 400: "Invalid Input", 500: "Internal Server Error"}
)
@api_view(['POST'])
def user_signup(request: Request) -> Response:
    """Handles the POST request for user signup."""
    try:  
        user : UserModel = user_sign_up(request)
        return Response(user
                    , status=status.HTTP_201_CREATED)

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
    request_body=UserSerializer,
    responses={200: 'Updated successfully', 400: 'Bad Request'}
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request: Request) -> Response:
    """Update user details including email and password."""
    user = request.user  # Authenticated user   
    # Call the helper function and return the response
    return update_user_details(user, request.data)


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
    user = request.user  # Get the authenticated user
    user_id = request.data.get('user_id')  # Get the user ID if provided (for admins)

    # Call the helper function to handle the logic and return the response
    return deactivate_user_account(user, user_id)
    

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
    Blacklists the refresh token and access token to log out the user.
    """
    refresh_token = request.data.get('refresh_token')
    access_token = request.headers.get('Authorization', '').replace('Bearer ', '')

    # Validate the presence of the refresh token
    if not refresh_token:
        return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Call the helper function to blacklist the tokens
    return blacklist_tokens(refresh_token, access_token)
    

@swagger_auto_schema(
    method='post',
    request_body=SellerSerializer,
    responses={
        201: "Seller profile created successfully. Pending admin approval.",
        400: "Bad request. Invalid data.",
        403: "Forbidden. Only 'end_user' can create a seller profile.",
        500: "Server error.",
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_seller(request) -> Response:
    """
    Creates a seller profile for the authenticated user if they are an 'end_user'.
    If successful, sends an approval request to the admin.
    """
    user = request.user  # Get the authenticated user

    # Call the helper function to create the seller profile
    return create_seller_profile(user, request.data)


@swagger_auto_schema(
    method='put',
    request_body=SellerSerializer,
    responses={
        201: "Seller profile Updated successfully.",
        400: "Bad request. Invalid data.",
        500: "Server error.",
    }
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_seller(request):
    try:
        serializer = get_seller_profile_and_update(request.user, request.data)
        return Response(
            {"message": "Seller profile updated successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )
    except serializers.ValidationError as e:
        return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "latitude",
            openapi.IN_QUERY,
            description="Latitude of the user",
            type=openapi.TYPE_NUMBER,
            required=True,
        ),
        openapi.Parameter(
            "longitude",
            openapi.IN_QUERY,
            description="Longitude of the user",
            type=openapi.TYPE_NUMBER,
            required=True,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number for pagination (default is 1).",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "page_size",
            openapi.IN_QUERY,
            description="Number of items per page (default is 10, max is 50).",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
    ],
    responses={200: "Nearby sellers fetched successfully."},
)
@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def fetch_nearby_sellers(request):
    try:
        # Extract latitude and longitude from query parameters
        user_lat = float(request.query_params.get("latitude"))
        user_lng = float(request.query_params.get("longitude"))
        page = int(request.query_params.get("page", 1))  # Default to page 1
        page_size = int(request.query_params.get("page_size", 10))  # Default to 10

        # Call the helper function to fetch nearby sellers
        nearby_sellers = get_nearby_sellers(user_lat, user_lng)

        # Paginate the results
        paginator = CustomPagination()
        paginator.page_size = page_size  # Set custom page size
        paginated_sellers = paginator.paginate_queryset(nearby_sellers, request)

        # Prepare paginated response data
        seller_data = [
            {"seller": SellerSerializer(seller[0]).data, "distance_km": seller[1]}
            for seller in paginated_sellers
        ]

        # Return paginated response
        return paginator.get_paginated_response(
            {"message": "Nearby sellers fetched successfully", "data": seller_data}
        )
    except ValueError as e:
        return Response(
            {"error": "Invalid input in query parameters", "details": str(e)}, status=400
        )
    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred", "details": str(e)}, status=500
        )
    


@swagger_auto_schema(
    method="delete",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "seller_id": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="ID of the seller to delete (required only for admin users).",
            ),
        },
        required=[],
    ),
    responses={
        204: "Seller deleted successfully.",
        403: "Permission denied. Only sellers or admins can delete.",
        404: "Seller not found.",
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_seller(request):
    """
    API to delete or deactivate a seller profile.
    - Sellers can delete their own profile.
    - Admins can delete a seller by specifying the seller ID.
    """
    try:
        # For admin, seller_id is taken from the request body
        seller_id = request.data.get("seller_id")
        
        # Call the helper function
        result = delete_seller_helper(request.user, seller_id=seller_id)

        # Return the success response
        return Response(result, status=204)

    except ValidationError as e:
        return Response({"error": str(e)}, status=400)
    except PermissionDenied as e:
        return Response({"error": str(e)}, status=403)
    except NotFound as e:
        return Response({"error": str(e)}, status=404)
    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred.", "details": str(e)}, status=500
        )
    

@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "seller_id": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="ID of the seller to deactivate (required only for admin users).",
            ),
        },
        required=[],
    ),
    responses={
        200: "Seller deactivated successfully.",
        403: "Permission denied. Only sellers or admins can deactivate.",
        404: "Seller not found.",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deactivate_seller(request):
    """
    API to deactivate a seller profile.
    - Sellers can deactivate their own profile.
    - Admins can deactivate a seller by specifying the seller ID.
    """
    try:
        # For admin, seller_id is taken from the request body
        seller_id = request.data.get("seller_id")
        
        # Call the helper function
        result = deactivate_seller_helper(request.user, seller_id=seller_id)

        # Return the success response
        return Response(result, status=200)

    except ValidationError as e:
        return Response({"error": str(e)}, status=400)
    except PermissionDenied as e:
        return Response({"error": str(e)}, status=403)
    except NotFound as e:
        return Response({"error": str(e)}, status=404)
    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred.", "details": str(e)}, status=500
        )