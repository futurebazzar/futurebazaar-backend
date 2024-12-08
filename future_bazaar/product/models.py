# apps/products/models.py
from django.db import models
from user.models import Seller


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='custom_categories')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image = models.BinaryField(blank = False) 
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)  # Field to activate/deactivate the category
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def is_subcategory(self):
        return self.parent_category is not None    # If it has a parent category, it's a subcategory


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    # Linking product to seller
    seller_id = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='products')
    
    # Product details
    name = models.CharField(max_length=255, blank=False)
    title = models.TextField(max_length=255, blank=False)
    description = models.TextField(max_length=255, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True) 
    banner_image = models.BinaryField(blank=False)
    exclusives = models.CharField(max_length=255, blank=False)
    # Category for the product
    category_id = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    # Default category based on the seller type (Furniture, Electronics)
    default_category = models.CharField(max_length=100, choices=Seller.CATEGORY)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.seller_category or self.default_category})"
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.BinaryField()  # Storing the image as binary data
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"   

class HeroSection(models.Model):
    hero_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100,blank=True)
    section_name = models.CharField(max_length=100, blank=True)
    seller_id =  models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='seller_section')
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_section')
    priority = models.IntegerField()
    banner_image = models.BinaryField(blank=False)


