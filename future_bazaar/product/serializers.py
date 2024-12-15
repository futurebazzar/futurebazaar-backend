from rest_framework import serializers
import base64
from .models import Category, Seller

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