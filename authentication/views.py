from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
import secrets
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from .serializers import AuthUserModelSerializer
from datetime import datetime, timedelta, timezone as dt_timezone
from rest_framework import status
from rest_framework.views import APIView
from .services import save_user, authenticate_google_user

OAUTH_STATE_COOKIE = 'oauth_state'

@api_view(['GET'])
def googleApi(request):
    error = request.query_params.get('error')
    if error:
        return Response(
            {'detail': f'OAuth error: {error}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    returned_state = request.query_params.get('state')
    stored_state = request.COOKIES.get(OAUTH_STATE_COOKIE)

    if not returned_state or not stored_state or not secrets.compare_digest(
        returned_state, stored_state
    ):
        return Response(
            {'detail': 'OAuth state mismatch.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    code = request.query_params.get('code')
    if not code:
        return Response(
            {'detail': 'Missing authorization code.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.REDIRECT_URI,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
        }

        access_token_url = 'https://oauth2.googleapis.com/token'
        token_response = requests.post(access_token_url, data=data)
        google_token_info = token_response.json()

        if 'error' in google_token_info:
            return Response(
                {
                    'error': google_token_info.get(
                        'error_description', google_token_info['error']
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    except requests.exceptions.RequestException as e:
        return Response(
            {'error': f'Error getting access token: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    id_token = google_token_info.get('id_token')
    google_access_token = google_token_info.get('access_token')

    if not id_token or not google_access_token:
        return Response(
            {'detail': 'Missing id_token or access_token from Google.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        save_user_data = authenticate_google_user(id_token, google_access_token)
    except jwt.InvalidTokenError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

    save_user_data['user']['google_refresh_token'] = google_token_info.get('refresh_token')

    response = Response(save_user_data, status=status.HTTP_200_OK)
    response.delete_cookie(OAUTH_STATE_COOKIE, path='/')
    return response

@api_view(['POST'])
def refresh_google_access_token(request):
    if not request.data.get('refresh_token'):
        return Response({'Message': 'No refresh token found in request.'}, status=status.HTTP_400_BAD_REQUEST)
    
    refresh_token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': request.data.get('refresh_token'),
    }

    try:
        response = requests.post(refresh_token_url, data=data)
        token_info = response.json()

        if token_info.get('error') == "invalid_grant":
            return Response({'Detail': 'Login expired. Please sign in again.'}, status=status.HTTP_401_UNAUTHORIZED)
        elif token_info.get('error'):
            return Response({'Detail': f"Error during new access token process: {token_info['error_description']}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'access_token': token_info['access_token']}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"detail": f"Error refreshing access token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
class NeuroCreateUser(APIView):
    def post(self, request):
        auth_type = request.query_params.get('type')
        if auth_type not in ('signin', 'login'):
            return Response(
                {'Message': 'Query parameter "type" is required and must be "signin" or "login".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AuthUserModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        User = get_user_model()

        if auth_type == 'login':
            user = User.objects.filter(email=email).first()
            if not user or not user.check_password(password):
                return Response(
                    {'detail': 'Invalid email or password.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            return Response(save_user(user), status=status.HTTP_200_OK)

        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': 'User with this email already exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        create_kwargs = {'email': email, 'password': password}
        user = User.objects.create_user(**create_kwargs)
        return Response(save_user(user), status=status.HTTP_201_CREATED)
