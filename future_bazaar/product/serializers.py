from rest_framework import serializers
from .models import Category, Seller

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'name', 'description', 'image', 'parent_category', 'is_active']

    def create(self, validated_data):
        user = self.context['request'].user

        # Get the seller profile from the user
        seller = Seller.objects.get(user_id=user.user_id)

        # Check if a category with the same name already exists for this seller
        category_name = validated_data.get('name')
        existing_category = Category.objects.filter(seller=seller, name=category_name).first()

        if existing_category:
            raise serializers.ValidationError(f"A category with the name '{category_name}' already exists.")
        
        category = Category.objects.create(**validated_data)

        return category

