
class SellerAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'seller_category', 'distance_display', 'is_active']
    list_filter = ['seller_category', 'is_active']
    search_fields = ['business_name', 'business_address']

    # Set a reference point for distance calculation (e.g., your office or user's location)
    reference_point = (22.5726, 88.3639)  # Example: Kolkata coordinates

    def distance_display(self, obj):
        """
        Display the distance of the seller from the reference point in the admin.
        """
        if obj.geo_location_lat and obj.geo_location_lng:
            distance = obj.distance_from(*self.reference_point)
            return f"{distance:.2f} km"
        return "N/A"

    distance_display.short_description = "Distance (km)"

    def get_queryset(self, request):
        """
        Annotate queryset with distance to enable sorting.
        """
        qs = super().get_queryset(request)
        # Adding extra annotations for sorting if needed (example shown with raw lat/lng)
        return qs

    def get_ordering(self, request):
        """
        Set default ordering by distance.
        """
        return ['distance_display']