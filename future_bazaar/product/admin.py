# apps/products/admin.py
from django.contrib import admin
from .models import Category, Product, ProductImage, HeroSection
from django.contrib import admin
from .models import Category
from django import forms

class CategoryAdminForm(forms.ModelForm):
    # Add a field to upload files
    image_upload = forms.FileField(required=False, label="Upload Image")

    class Meta:
        model = Category
        fields = ['seller', 'name', 'description', 'parent_category', 'is_active', 'image_upload']

    def save(self, commit=True):
        # Override save method to handle BinaryField
        instance = super().save(commit=False)
        
        # Handle file upload if provided
        image_file = self.cleaned_data.get('image_upload')
        if image_file:
            instance.image = image_file.read()  # Convert file to binary data

        if commit:
            instance.save()

        return instance

class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ['name', 'seller', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']


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
