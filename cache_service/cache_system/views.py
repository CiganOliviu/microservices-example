import requests
import os
from django.core.cache import cache
from django.http import JsonResponse
from dotenv import load_dotenv

load_dotenv()
CRUD_SERVICE_URL = f"{os.getenv('CRUD_SERVICE')}/api/users/"


def cached_user_list(request):
    username = request.GET.get('username', None)
    cache_key = 'users_list'

    users = cache.get(cache_key)

    if not users:
        response = requests.get(CRUD_SERVICE_URL)
        if response.status_code == 200:
            users = response.json()
            cache.set(cache_key, users, timeout=60)
        else:
            return JsonResponse({'error': 'Failed to fetch users'}, status=500)

    if username:
        users = [user for user in users if user.get('username') == username]

    return JsonResponse(users, safe=False)
