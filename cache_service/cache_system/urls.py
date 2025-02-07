from django.urls import path
from .views import cached_user_list

urlpatterns = [
    path('cached-users/', cached_user_list),
]
