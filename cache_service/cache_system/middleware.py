from django.http import JsonResponse
import jwt

SECRET_KEY = "12fba565c7f26db68ff4ff1381424c2ece216466e625646f0830247a016e2bbea6302c2e840d4317ffb0faa28966eda01b0a6ee502be8fc3bec43041804a53b967fe470395e1ef76591be93c6190bb85ad3dd8d17aa1f31630aea28057505ff5f75dc7c6e6092262025ae32d74a223113e8f459e99bd43097a6c51698439a79cd439d5fd0dae5c0b54a4e1501a0dc9e49ff5b76e69bcea5a5c2e77a229ea3fb1f04e7eb9283bda1f41ff3e9517a9b5875bdbc21fe01230e4265263b5686825bfa0292c551cd75450da16d3369bff059a9f3ad77c18b1bcf9525be6a59b3faed33f49ae6876a0bbfb61f7bc3a0a881e8126154f02d899a0c639dee6a145623fbf"


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