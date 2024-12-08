# apps/products/admin.py
from django.contrib import admin
from .models import Category, Product, ProductImage, HeroSection

# Registering the Category model
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'parent_category', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'seller')
    search_fields = ('name', 'seller__business_name')

# Registering the Product model
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller_id', 'price', 'stock_quantity', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'category_id', 'seller_id')
    search_fields = ('name', 'description', 'seller_id__business_name')

# Registering the ProductImage model
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'created_at')
    list_filter = ('product',)
    search_fields = ('product__name',)

# Registering the HeroSection model
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller_id', 'product_id', 'priority')
    list_filter = ('priority', 'seller_id', 'product_id')
    search_fields = ('name', 'seller_id__business_name', 'product_id__name')

# Registering models with the Django admin site
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(HeroSection, HeroSectionAdmin)
