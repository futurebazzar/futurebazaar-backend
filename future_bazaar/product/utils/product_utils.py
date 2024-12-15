from rest_framework.exceptions import PermissionDenied, ValidationError,NotFound
from rest_framework.views import exception_handler
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from ..models import Category, Seller
from ..serializers import CategorySerializer
from rest_framework.permissions import IsAuthenticated
from user.models import UserModel   
from ..decorators import restrict_user_type
import logging


logger = logging.getLogger(__name__)

def create_category_helper(request):
    """
    Helper function to create a new category for a seller.
    """
    # Serialize and validate the data
    serializer = CategorySerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    file = request.FILES.get('image')  # 'image' is the field name in the frontend form

    if file:
        # Read the file content into binary format
        file_binary = file.read()

    # Check if a category with the same name already exists
    category_name = serializer.validated_data.get('name')
    existing_category = Category.objects.filter(name=category_name).first()
    if existing_category:
        raise ValidationError(f"A category with the name '{category_name}' already exists for this seller.")
    # Save the validated category and associate it with the seller
    serializer.validated_data['image'] = file_binary
    category = serializer.save()
    
    return category


def get_category_helper(user, category_id):
    """
    Helper function to fetch a category by ID for a seller.
    """
    # Check if the user has a seller profile
    if not hasattr(user, 'seller_profile'):
        logger.warning(f"Unauthorized access attempt by user ID {user.id}")
        raise PermissionDenied("Only users with Seller profiles can access categories.")

    # Fetch the category associated with the logged-in seller
    try:
        category = Category.objects.get(category_id=category_id, seller=user.seller_profile)
    except Category.DoesNotExist:
        logger.error(f"Category with ID {category_id} not found for Seller ID {user.seller_profile.seller_id}")
        raise NotFound(f"Category with ID {category_id} does not exist.")

    return category


def update_category_helper(request, category_id):
    """
    Helper function to update a category for a seller.
    """
    print(request.user)
    # Check if the user has a seller profile
    seller = Seller.objects.get(user_id=request.user.user_id)
    print(request.user.user_id)
    # Fetch the category
    try:
        category = Category.objects.get(pk=category_id, seller=seller.seller_id)
    except Category.DoesNotExist:
        logger.error(f"Category ID {category_id} not found or not owned by user ID {request.user.user_id}")
        raise NotFound("Category not found or not owned by the current seller.")

    # Serialize and validate the data
    serializer = CategorySerializer(category, data=request.data, partial=True, context={'request': request})
    serializer.is_valid(raise_exception=True)

    # Save the updated category
    category = serializer.save()
    return category


def delete_category_helper(user, category_id):
    """
    Helper function to delete a category for a seller.
    """
    # Fetch the category
    try:
        category = Category.objects.get(pk=category_id, seller=user.seller_profile)
    except Category.DoesNotExist:
        logger.error(f"Category ID {category_id} not found or not owned by user ID {user.id}")
        raise NotFound("Category not found or not owned by the current seller.")

    # Delete the category
    category.delete()
    return True