import jwt
import os
from django.http import JsonResponse
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')


def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                user_data = decode_token(token)
                if user_data:
                    request.user = user_data
                else:
                    return JsonResponse({'error': 'Invalid token'}, status=401)
            except ValueError as e:
                return JsonResponse({'error': str(e)}, status=401)

        return self.get_response(request)