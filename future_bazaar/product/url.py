from django.urls import path
from .views import create_category,get_category,update_category,delete_category,get_categories_with_children
from .views import create_category,get_category,update_category,delete_category, create_product

urlpatterns = [
    path('category/', create_category, name='create_category'),
    path('category/<int:category_id>/', get_category, name='get_category'),
    path('category/update/<int:category_id>/', update_category, name='update_category'),
    path('category/<int:category_id>/delete/', delete_category, name='delete_category'),
    path('categories/hierarchical/', get_categories_with_children, name='categories-hierarchical'),
    path('product/create/', create_product, name='create_product'),
]
