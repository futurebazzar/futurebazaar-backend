from rest_framework.exceptions import PermissionDenied, ValidationError,NotFound
from rest_framework.views import exception_handler
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Seller
from .serializers import CategorySerializer
from rest_framework.permissions import IsAuthenticated
from user.models import UserModel   
from .decorators import restrict_user_type
import logging

# DRF Extensions
from drf_yasg.utils import swagger_auto_schema

logger = logging.getLogger(__name__)

@swagger_auto_schema(
    method='post',
    request_body=CategorySerializer,
    responses={
        201: "Category created successfully",
        400: "Bad Request",
        403: "Forbidden",
        500: "Internal Server Error",
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
#@restrict_user_type('Seller')  # Only 'Seller' users can access this view
def create_category(request):
    """
    API to create a new category. Only users with Seller profiles can create categories.
    """

    try:
        user = request.user

        # Serialize and validate the data
        serializer = CategorySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)  # Automatically raises ValidationError for invalid data

        # Check if a category with the same name already exists for this seller
        category_name = serializer.validated_data.get('name')
        #seller = user.seller_profile  # Get the seller profile directly from the user object
        #print(seller)
        print(category_name)

        # Check for existing category with the same name
        existing_category = Category.objects.filter( name=category_name).first()
        if existing_category:
            raise ValidationError(f"A category with the name '{category_name}' already exists for this seller.")

        # Save the validated category and associate it with the seller
        category = serializer.save()
        print(category)

        # Return a success response with the category data
        return Response({
            "message": "Category created successfully",
            "data": serializer.data,
        }, status=status.HTTP_201_CREATED)

    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        return Response({"error": ve.detail}, status=status.HTTP_400_BAD_REQUEST)

    except PermissionDenied as pd:
        logger.warning(f"Permission denied: {pd}")
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return Response({"error": "An unexpected error occurred. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_category(request, category_id: int) -> Response:
    """
    API to fetch a single category by ID.
    Only users with Seller profiles can access this API.
    """
    user: UserModel = request.user

    # Check if the user is a Seller
    if not hasattr(user, 'seller_profile'):
        logger.warning(f"Unauthorized access attempt by user ID {user.user_id}")
        raise PermissionDenied("Only users with Seller profiles can access categories.")

    seller = user.seller_profile  # Access the Seller profile of the user

    try:
        # Fetch the category associated with the logged-in seller
        category: Category = Category.objects.get(category_id=category_id, seller=seller)
    except Category.DoesNotExist:
        logger.error(f"Category with ID {category_id} not found for Seller ID {seller.seller_id}")
        raise NotFound(f"Category with ID {category_id} does not exist.")

    # Serialize and return the category
    serializer = CategorySerializer(category)
    return Response({
        "message": "Category fetched successfully.",
        "data": serializer.data
    }, status=status.HTTP_200_OK)