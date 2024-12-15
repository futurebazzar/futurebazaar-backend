from rest_framework.exceptions import PermissionDenied, ValidationError,NotFound
from rest_framework.views import exception_handler
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Seller
from .serializers import CategorySerializer
from rest_framework.permissions import IsAuthenticated
from user.models import UserModel   
from .decorators import restrict_user_type
from .utils.product_utils import (create_category_helper,get_category_helper,update_category_helper,delete_category_helper)
import logging
from drf_yasg import openapi 
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.parsers import MultiPartParser, FormParser
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
 # Only 'Seller' users can access this view
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@restrict_user_type('Seller')
@parser_classes([MultiPartParser, FormParser])
def create_category(request):
    try:
       
        category = create_category_helper(request)
        return Response({
            "message": "Category created successfully",
            "data": CategorySerializer(category).data,
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
def get_category(request, category_id: int):
    try:
        category = get_category_helper(request.user, category_id)
        return Response({
            "message": "Category fetched successfully.",
            "data": CategorySerializer(category).data,
        }, status=status.HTTP_200_OK)

    except PermissionDenied as pd:
        logger.warning(f"Permission denied: {pd}")
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)

    except NotFound as nf:
        logger.error(f"Not found: {nf}")
        return Response({"error": str(nf)}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return Response({"error": "An unexpected error occurred. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='put',
    request_body=CategorySerializer,
    responses={
        200: "Category updated successfully",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        500: "Internal Server Error",
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@restrict_user_type('Seller') 
def update_category(request, category_id):
    try:
        print(request.user)
        category = update_category_helper(request, category_id)
        return Response({
            "message": "Category updated successfully",
            "data": CategorySerializer(category).data,
        }, status=status.HTTP_200_OK)

    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        return Response({"error": ve.detail}, status=status.HTTP_400_BAD_REQUEST)

    except PermissionDenied as pd:
        logger.warning(f"Permission denied: {pd}")
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)

    except NotFound as nf:
        logger.error(f"Not found: {nf}")
        return Response({"error": str(nf)}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return Response({"error": "An unexpected error occurred. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@swagger_auto_schema(
    method='delete',
    responses={
        200: "Category deleted successfully",
        403: "Forbidden",
        404: "Not Found",
        500: "Internal Server Error",
    }
)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@restrict_user_type('Seller') 
def delete_category(request, category_id):
    try:
        delete_category_helper(request.user, category_id)
        return Response({
            "message": "Category deleted successfully",
        }, status=status.HTTP_200_OK)

    except PermissionDenied as pd:
        logger.warning(f"Permission denied: {pd}")
        return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)

    except NotFound as nf:
        logger.error(f"Not found: {nf}")
        return Response({"error": str(nf)}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return Response({"error": "An unexpected error occurred. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary="Get seller's categories with subcategories",
    operation_description=(
        "Retrieve all parent categories for the authenticated seller along with their child categories."
    ),
    responses={
        200: openapi.Response(
            description="Categories retrieved successfully",
            examples={
                "application/json": [
                    {
                        "category_id": 1,
                        "name": "Bedroom",
                        "description": "Furniture for bedrooms.",
                        "image": "binary_data",
                        "parent_category": None,
                        "is_active": True,
                        "subcategories": [
                            {
                                "category_id": 2,
                                "name": "4x6 Bed",
                                "description": "Small-sized bed.",
                                "image": "binary_data",
                                "parent_category": 1,
                                "is_active": True
                            },
                            {
                                "category_id": 3,
                                "name": "6x6 Bed",
                                "description": "Large-sized bed.",
                                "image": "binary_data",
                                "parent_category": 1,
                                "is_active": True
                            }
                        ]
                    }
                ]
            },
        ),
        403: "Forbidden: You do not have permission to access this resource.",
        404: "Not Found: Seller profile does not exist for the user.",
        500: "Internal Server Error: An unexpected error occurred.",
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_categories_with_children(request):
    try:
        # Get the authenticated user
        user = request.user
        print(user.user_id)
        # Retrieve the seller profile associated with the user
        try:
            seller = Seller.objects.get(user_id=request.user.user_id) 
            print(seller)  
        except ObjectDoesNotExist:
            return Response(
                {"error": "Seller profile does not exist for the user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fetch parent categories with parent_category as None or 0
        parent_categories = Category.objects.filter(
            seller_id=seller.seller_id,
            parent_category__isnull=True
        ) | Category.objects.filter(
            seller=seller,
            parent_category=0
        )

        # Structure the response to include subcategories for each parent
        categories_with_children = []
        for parent in parent_categories:
            # Fetch subcategories for the current parent
            subcategories = Category.objects.filter(parent_category=parent)
            parent_data = CategorySerializer(parent).data
            parent_data['subcategories'] = CategorySerializer(subcategories, many=True).data
            categories_with_children.append(parent_data)

        return Response(categories_with_children, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )