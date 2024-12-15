from rest_framework import serializers
from .models import UserModel, Seller
from rest_framework.pagination import PageNumberPagination

class UserSerializer(serializers.ModelSerializer):
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
    
    def update(self, instance: UserModel, validated_data: dict) -> UserModel:
        """Update user details, including password and email."""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.password = password  # Already hashed
        instance.save()
        return instance
    

class UserLoginRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True, help_text="The username or email of the user.")
    password = serializers.CharField(required=True, write_only=True, help_text="The password of the user.")

class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True, help_text="refresh token of the user")



class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = [
            "business_name",
            "business_address",
            "business_contact_number",
            "bussiness_email",
            "seller_category",
            "shop_description",
            "shop_timing_open",
            "shop_timing_close",
            "shop_location",
            "geo_location_lng",
            "geo_location_lat",
            "shop_photo",
            "days_closed",
            "gst_number",
        ]

    # def validate_business_contact_number(self, value: str) -> str:
    #     """
    #     Ensure the contact number is numeric and has a valid length.
    #     """
    #     if not value.isdigit():
    #         raise serializers.ValidationError("Business contact number must be numeric.")
    #     if len(value) < 10 or len(value) > 15:
    #         raise serializers.ValidationError("Contact number must be between 10 and 15 digits.")
    #     return value

    # def validate_shop_timing_close(self, value) -> str:
    #     """
    #     Ensure shop_timing_close is later than shop_timing_open.
    #     """
    #     shop_timing_open = self.initial_data.get("shop_timing_open")
    #     if shop_timing_open and value <= shop_timing_open:
    #         raise serializers.ValidationError("Closing time must be after opening time.")
    #     return value

    # def validate_geo_location(self, value: str) -> str:
    #     """
    #     Validate geo_location format (latitude,longitude).
    #     """
    #     try:
    #         lat, lon = map(float, value.split(","))
    #         if not (-90 <= lat <= 90 and -180 <= lon <= 180):
    #             raise serializers.ValidationError("Invalid latitude or longitude values.")
    #     except (ValueError, TypeError):
    #         raise serializers.ValidationError(
    #             "Geo location must be in 'latitude,longitude' format (e.g., '37.7749,-122.4194')."
    #         )
    #     return value

    # def validate_shop_photo(self, value) -> str:
    #     """
    #     Validate that the shop photo is not empty.
    #     """
    #     if not value:
    #         raise serializers.ValidationError("Shop photo is required.")
    #     # Optionally add size/type validation if needed.
    #     return value

    # def validate_bussiness_email(self, value: str) -> str:
    #     """
    #     Ensure business email is in a valid email format or empty.
    #     """
    #     if value and "@" not in value:
    #         raise serializers.ValidationError("Enter a valid email address.")
    #     return value

    # def validate(self, data: dict) -> dict:
    #     """
    #     Custom validation for interdependent fields.
    #     """
    #     if data.get("seller_category") not in ["electronic", "furniture"]:
    #         raise serializers.ValidationError(
    #             {"seller_category": "Seller category must be either 'electronic' or 'furniture'."}
    #         )
    #     return data
    
    def create(self, validated_data: dict) -> Seller:
        seller = Seller(**validated_data)
        
        seller.save()
        return seller
    
    def update(self, instance: UserModel, validated_data: dict) -> UserModel:
        """Update user details, including password and email."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value) # Already hashed
        instance.save()
        return instance
    
class CustomPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page
    page_size_query_param = "page_size"  # Allow client to control page size
    max_page_size = 50  # Maximum allowed page size

    
UserType = {
     
        'admin': 'Admin',
        'seller': 'Seller',
        'end_user': 'End User',
    
}
