import json
import jwt
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from datetime import datetime, timedelta
from django.core.cache import cache


SECRET_KEY = "12fba565c7f26db68ff4ff1381424c2ece216466e625646f0830247a016e2bbea6302c2e840d4317ffb0faa28966eda01b0a6ee502be8fc3bec43041804a53b967fe470395e1ef76591be93c6190bb85ad3dd8d17aa1f31630aea28057505ff5f75dc7c6e6092262025ae32d74a223113e8f459e99bd43097a6c51698439a79cd439d5fd0dae5c0b54a4e1501a0dc9e49ff5b76e69bcea5a5c2e77a229ea3fb1f04e7eb9283bda1f41ff3e9517a9b5875bdbc21fe01230e4265263b5686825bfa0292c551cd75450da16d3369bff059a9f3ad77c18b1bcf9525be6a59b3faed33f49ae6876a0bbfb61f7bc3a0a881e8126154f02d899a0c639dee6a145623fbf"
CRUD_SERVICE_URL = "http://cache-service:8001/api/cached-users/"


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