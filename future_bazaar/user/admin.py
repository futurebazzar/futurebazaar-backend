# apps/users/admin.py
from django.contrib import admin
from .models import UserModel, Seller
from ipware import get_client_ip
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Registering the UserModel (custom user model)
class UserModelAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'created_date')
    list_filter = ('user_type', 'is_active')
    search_fields = ('email', 'first_name')

    
# Registering the Seller model
class SellerAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user_id', 'seller_category', 'is_approved', 'is_active','distance_from_admin', 'created_at')
    list_filter = ('seller_category', 'is_approved', 'is_active')
    search_fields = ('business_name', 'user_id__email', 'business_contact_number')
    actions = ['approve_seller', 'reject_seller']

    
    def approve_seller(self, request, queryset):
        """Mark selected seller profiles as approved and notify the seller."""
        for seller in queryset:
            seller.is_approved = True
            seller.is_active = True
            seller.save()
            
        
        self.message_user(request, "Selected seller profiles have been approved.")
    
    def reject_seller(self, request, queryset):
        """Reject selected seller profiles."""
        queryset.update(is_approved=False)
        queryset.update(is_active=False)
        self.message_user(request, "Selected seller profiles have been rejected.")

    def get_admin_location(self, request):
        """
        Retrieve the admin's approximate location using their IP address.
        """
        # Get the client's IP address
        ip, is_routable = get_client_ip(request)
        if ip is None:
            return None  # Unable to determine IP address

        try:
            # Use Nominatim or another geolocation service to get coordinates
            geolocator = Nominatim(user_agent="django-admin-location")
            location = geolocator.geocode(ip)
            if location:
                return location.latitude, location.longitude
        except Exception as e:
            print(f"Error fetching admin location: {str(e)}")
            return None

    def distance_from_admin(self, obj):
        """
        Calculate the distance of the seller from the admin's location.
        """
        # Use the admin's request object to fetch the IP-based location
        admin_location = self.get_admin_location(self.request)

        # Validate both admin and seller location exist
        if admin_location and obj.geo_location_lat and obj.geo_location_lng:
            seller_location = (obj.geo_location_lat, obj.geo_location_lng)
            distance = geodesic(admin_location, seller_location).kilometers
            return f"{distance:.2f} km"
        return "N/A"

    distance_from_admin.short_description = "Distance (km)"  # Column header in admin table

    def changelist_view(self, request, extra_context=None):
        """
        Override changelist_view to attach the request object for distance calculation.
        """
        self.request = request
        return super().changelist_view(request, extra_context=extra_context)
    approve_seller.short_description = "Approve selected seller profiles"
    reject_seller.short_description = "Reject selected seller profiles"




# Register the models with Django admin
admin.site.register(UserModel, UserModelAdmin)
admin.site.register(Seller, SellerAdmin)
