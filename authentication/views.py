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
from .services import save_user, verify_google_id_token
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['GET'])
def googleApi(request):
    error = request.query_params.get('error')
    if error:
        return Response(
            {'detail': f'OAuth error: {error}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    code = request.query_params.get('code')
    if not code:
        return Response(
            {'detail': 'Missing authorization code.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.REDIRECT_URI,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
    }

    access_token_url = 'https://oauth2.googleapis.com/token'
    token_response = requests.post(access_token_url, data=data)
    google_token_info  = token_response.json()

    if 'error' in google_token_info:
        return Response(
            {'error': google_token_info.get('error_description', google_token_info['error'])},
            status=status.HTTP_400_BAD_REQUEST,
        )

    id_token = google_token_info.get('id_token')

    if not id_token:
        return Response(
            {'detail': 'Missing id_token.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    save_user_data = verify_google_id_token(id_token)

    response = Response(save_user_data, status=status.HTTP_200_OK)
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
        response = requests.pos(refresh_token_url, data=data)
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
        serializer = AuthUserModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        User = get_user_model()
        auth_type = request.query_params.get('type')
        if auth_type == 'login':            
            user = User.objects.filter(email=email).exists()
            if not user:
                return Response(
                    {'detail': 'User with this email does not exist.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user = User.objects.filter(email=email).first()

            if not user.check_password(password):
                return Response(
                    {'detail': 'Invalid password.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            jwt_data = RefreshToken.for_user(user)

            return Response({
                "user": serializer.data, 
                "jwt_data": {
                    "access": str(jwt_data.access_token),
                    "refresh": str(jwt_data),
                }}, status=status.HTTP_200_OK)
        elif auth_type == 'signup':
            if User.objects.filter(email=email).exists():
                return Response(
                    {'detail': 'User with this email already exists.'},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(save_user({"email": email, "password": password}, auth_provider='password'), status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'Message': 'Query parameter "type" is required and must be "signup" or "login".'},
                status=status.HTTP_400_BAD_REQUEST
            )