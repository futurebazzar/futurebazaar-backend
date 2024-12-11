from django.urls import path
from .views import create_category,get_category

urlpatterns = [
    path('category/', create_category, name='create_category'),
    path('category/<int:category_id>/', get_category, name='get_category'),
]
