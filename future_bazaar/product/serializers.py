from rest_framework import serializers
import base64
from .models import Category, Seller
from .models import Category, Seller, Product

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)
    image_base64 = serializers.SerializerMethodField() 
    class Meta:
        model = Category
        fields = ['category_id', 'name', 'description', 'image', 'image_base64', 'parent_category', 'is_active']

    def get_image_base64(self, obj):
        if obj.image:
            # Convert binary data to base64
            encoded_image = base64.b64encode(obj.image).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded_image}"  # You can modify the mime type (jpeg/png) accordingly
        return None
    

    def create(self, validated_data):
        user = self.context['request'].user
        # Get the seller profile from the user
        try:
            seller = Seller.objects.get(user_id=user.user_id)
        except Seller.DoesNotExist:
            raise serializers.ValidationError("Seller profile does not exist for the user.")

        # Check if a category with the same name already exists for this seller
        category_name = validated_data.get('name')
        if Category.objects.filter(seller=seller, name=category_name).exists():
            raise serializers.ValidationError(f"A category with the name '{category_name}' already exists.")

        # Create the category
        category = Category.objects.create(seller=seller, **validated_data)
        return category

    def update(self, instance, validated_data):
        # Prevent changing the seller
        if 'seller' in validated_data:
            validated_data.pop('seller')

        # Prevent duplicate category names for the same seller
        category_name = validated_data.get('name', instance.name)
        seller = instance.seller
        if Category.objects.filter(seller=seller, name=category_name).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(f"A category with the name '{category_name}' already exists.")

        # Update and save the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class ProductSerializer(serializers.ModelSerializer):
    banner_image = serializers.FileField(required=False) 

    class Meta:
        model = Product
        fields = [
            'name', 'title', 'description', 
            'price', 'discounted_price', 'stock_quantity', 'banner_image', 
            'exclusives'
        ]
        read_only_fields = ['product_id', 'created_at', 'updated_at', 'category_id']  # These fields are read-only

    def validate(self, attrs) :
        """
        Custom validation for the product.
        """
        user = self.context['request'].user
        if user.user_type != 'seller':
            raise serializers.ValidationError("Only sellers can create products.")
        
        # Automatically link the seller from the authenticated user
        if 'seller_id' in attrs:
            if attrs['seller_id'] != user.seller.id:
                raise serializers.ValidationError("Seller ID does not match the authenticated user's seller.")

        # Validate that the discounted price is not greater than the price
        if attrs.get('discounted_price') and attrs['discounted_price'] > attrs['price']:
            raise serializers.ValidationError("Discounted price cannot be higher than the price.")
        
        return attrs

    def create(self, validated_data) -> Product:
        """
        Create and return a new product instance.
        """
        user = self.context['request'].user
        validated_data['seller_id'] = user.seller  # Automatically link the seller from the authenticated user
        validated_data['is_active'] = True  # Set is_active to True by default
        return super().create(validated_data)