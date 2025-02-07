from django.urls import path
from .views import login, verify_token, logout

urlpatterns = [
    path('auth/login/', login),
    path('auth/verify/', verify_token),
    path('auth/logout/', logout),
]
