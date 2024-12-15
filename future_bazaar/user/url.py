from django.urls import path
from .views import user_signup, login_user, public_api, private_api,update_user, deactivate_user, logout_user, create_seller, update_seller, fetch_nearby_sellers, deactivate_seller, delete_seller
urlpatterns = [
    path('api/v1/signup', user_signup),
    path('api/v1/login/', login_user, name='login_user'),
    path('api/v1/public', public_api, name='public_api'),
    path('api/v1/private', private_api, name='private_api'),
    path('api/v1/update/', update_user, name='update_user'),
    path('api/v1/deactivate/', deactivate_user, name='deactivate_user'),
    path('api/v1/logout/', logout_user, name='logout'),
    path('api/v1/create-seller/', create_seller, name='create_seller'),
    path('api/v1/update-seller/', update_seller, name='update_seller'),
    path("api/v1/sellers/nearby/", fetch_nearby_sellers, name="fetch_nearby_sellers"),
    path("api/v1/sellers/deactivate/", deactivate_seller, name="deactivate_seller"),
    path("api/v1/sellers/delete/", delete_seller, name="delete_seller"),
]
