import json
import jwt
import requests
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from datetime import datetime, timedelta
from django.core.cache import cache
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
CRUD_SERVICE_URL = f"{os.getenv('CACHE_SERVICE')}/api/cached-users/"


def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


@csrf_exempt
def login(request):
    try:
        body = json.loads(request.body)
        username = body.get('username')
        password = body.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)

        response = requests.get(f"{CRUD_SERVICE_URL}?username={username}")
        if response.status_code != 200 or not response.json():
            return JsonResponse({'error': 'Status code not 200 or not json response'}, status=401)

        user_data = response.json()[0]

        if not check_password(password, user_data['password']):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        payload = {
            'id': user_data['id'],
            'username': user_data['username'],
            'exp': datetime.utcnow() + timedelta(hours=1),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        cache.set(f'token_{user_data["id"]}', token, timeout=3600)

        return JsonResponse({'token': token})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
def verify_token(request):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization header missing or invalid'}, status=401)

        token = auth_header.split(' ')[1]
        payload = decode_token(token)

        cached_token = cache.get(f'token_{payload["id"]}')
        if cached_token != token:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        return JsonResponse({'user': payload})

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=401)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def logout(request):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization header missing or invalid'}, status=401)

        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        cache.delete(f'token_{payload["id"]}')

        return JsonResponse({'message': 'Successfully logged out'}, status=200)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)