# apps/users/admin.py
from django.contrib import admin
from .models import UserModel, Seller

# Registering the UserModel (custom user model)
class UserModelAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'created_date', 'updated_date')
    list_filter = ('user_type', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')

# Registering the Seller model
class SellerAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user_id', 'seller_category', 'is_approved', 'is_active', 'created_at', 'upadated_date')
    list_filter = ('seller_category', 'is_approved', 'is_active')
    search_fields = ('business_name', 'user_id__email', 'business_contact_number')

# Register the models with Django admin
admin.site.register(UserModel, UserModelAdmin)
admin.site.register(Seller, SellerAdmin)
