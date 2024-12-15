from ..serializers import UserSerializer, SellerSerializer
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from typing import Optional
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError, PermissionDenied
from ..models import UserModel, BlacklistedAccessToken, Seller
from rest_framework.exceptions import NotFound, ValidationError
from typing import Union
from rest_framework import serializers
from geopy.distance import geodesic




def hash_password(password: str) -> str:
    """Hash the user's password securely."""
    return make_password(password)

def user_sign_up(request: Request) -> Optional[Response]:
    """Handles user signup logic."""

    serializer = UserSerializer(data=request.data)
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
    serializer = UserSerializer(user, data=data, partial=True)

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
        if user.user_type == "seller":
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

        #     send_mail(
        #     subject="New Seller Profile Created",
        #     message=f"A new seller profile has been created by {user.first_name} {user.last_name}. "
        #             f"Please review and approve/reject it in the admin dashboard.",
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[settings.ADMIN_EMAIL],  # You can set your admin email here
        # )

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
    
    
def get_seller_profile_and_update(user, data):
    """Helper function to retrieve and update seller profile."""
    if user.user_type != "seller":
        raise serializers.ValidationError("Only users with type 'seller' can update a seller profile.")

    try:
        seller_profile = Seller.objects.get(user_id=user.id)
    except Seller.DoesNotExist:
        raise serializers.ValidationError("Seller profile does not exist for this user.")

    serializer = SellerSerializer(instance=seller_profile, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return serializer




def get_nearby_sellers(user_lat: float, user_lng: float):
    """
    Fetch nearby sellers within a 30 km radius, sorted by distance.
    """
    user_location = (user_lat, user_lng)
    nearby_sellers = []

    for seller in Seller.objects.all():
        seller_location = (seller.geo_location_lat, seller.geo_location_lng)
        distance_km = geodesic(user_location, seller_location).km
        print("dista",distance_km)
        if distance_km <= 40:  # Within 30 km radius
            nearby_sellers.append((seller, distance_km))

    return sorted(nearby_sellers, key=lambda x: x[1])



def delete_seller_helper(user, seller_id=None):

    user_type = getattr(user, "user_type", None)  # Assuming `user_type` exists on User model

    # Seller: Delete their own profile
    if user_type == "seller":
        try:
            seller = Seller.objects.get(user=user)  # Assuming `Seller` links to `User`
            seller.delete()
            return {"message": "Your profile has been successfully deleted."}
        except Seller.DoesNotExist:
            raise NotFound("Seller profile not found for the authenticated user.")

    # Admin: Delete a specific seller profile
    elif user_type == "admin":
        if not seller_id:
            raise ValidationError("Seller ID is required for admin deletion.")

        try:
            seller = Seller.objects.get(id=seller_id)
            seller.delete()
            return {"message": f"Seller with ID {seller_id} has been successfully deleted."}
        except Seller.DoesNotExist:
            raise NotFound(f"Seller with ID {seller_id} does not exist.")

    # Unauthorized user
    else:
        raise PermissionDenied("Permission denied. Only sellers or admins can delete.")
    


def deactivate_seller_helper(user, seller_id=None):
    """
    Helper function to handle the deactivation of seller profiles.

    Args:
        user: The authenticated user making the request.
        seller_id (int, optional): ID of the seller to deactivate (required for admin users).

    Returns:
        dict: A success message with details about the deactivated profile.

    Raises:
        PermissionDenied: If the user lacks permissions to deactivate.
        NotFound: If the seller profile does not exist.
        ValidationError: If the admin does not provide a seller_id.
    """
    user_type = getattr(user, "user_type", None)  # Assuming `user_type` exists on User model

    # Seller: Deactivate their own profile
    if user_type == "seller":
        try:
            seller = Seller.objects.get(user=user)  # Assuming `Seller` links to `User`
            seller.is_active = False
            seller.save()
            return {"message": "Your profile has been successfully deactivated."}
        except Seller.DoesNotExist:
            raise NotFound("Seller profile not found for the authenticated user.")

    # Admin: Deactivate a specific seller profile
    elif user_type == "admin":
        if not seller_id:
            raise ValidationError("Seller ID is required for admin deactivation.")

        try:
            seller = Seller.objects.get(id=seller_id)
            seller.is_active = False
            seller.save()
            return {"message": f"Seller with ID {seller_id} has been successfully deactivated."}
        except Seller.DoesNotExist:
            raise NotFound(f"Seller with ID {seller_id} does not exist.")

    # Unauthorized user
    else:
        raise PermissionDenied("Permission denied. Only sellers or admins can deactivate.")
    


