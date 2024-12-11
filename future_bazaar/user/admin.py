# apps/users/admin.py
from django.contrib import admin
from .models import UserModel, Seller

# Registering the UserModel (custom user model)
class UserModelAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'created_date', 'updated_date')
    list_filter = ('user_type', 'is_active')
    search_fields = ('email', 'first_name')

# Registering the Seller model
class SellerAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user_id', 'seller_category', 'is_approved', 'is_active', 'created_at', 'updated_date')
    list_filter = ('seller_category', 'is_approved', 'is_active')
    search_fields = ('business_name', 'user_id__email', 'business_contact_number')
    actions = ['approve_seller', 'reject_seller']

    def approve_seller(self, request, queryset):
        """Mark selected seller profiles as approved."""
        queryset.update(is_approved=True, is_active = True)
        self.message_user(request, "Selected seller profiles have been approved.")
    
    def reject_seller(self, request, queryset):
        """Reject selected seller profiles."""
        queryset.update(is_approved=False)
        self.message_user(request, "Selected seller profiles have been rejected.")
    
    approve_seller.short_description = "Approve selected seller profiles"
    reject_seller.short_description = "Reject selected seller profiles"



# Register the models with Django admin
admin.site.register(UserModel, UserModelAdmin)
admin.site.register(Seller, SellerAdmin)
