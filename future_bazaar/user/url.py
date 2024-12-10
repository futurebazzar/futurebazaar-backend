from django.urls import path, include
from .views import user_signup, login_user, public_api, private_api,update_user, deactivate_user, logout_user

urlpatterns = [
    path('api/v1/signup', user_signup),
    path('api/v1/login/', login_user, name='login_user'),
    path('api/v1/public', public_api, name='public_api'),
    path('api/v1/private', private_api, name='private_api'),
    path('api/v1/update/', update_user, name='update_user'),
    path('api/v1/deactivate/', deactivate_user, name='deactivate_user'),
     path('api/v1/logout/', logout_user, name='logout'),
]
