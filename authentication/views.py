from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from .serializers import AuthUserModelSerializer, GoogleAuthUserModelSerializer
from datetime import datetime, timedelta, timezone as dt_timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from .services import save_user

@api_view(['POST'])
def googleApi(request):
    code = request.data.get('code')
    error = request.data.get('error')

    if not code or error:
        return Response(f"Missing code or received error: {error}", status=status.HTTP_400_BAD_REQUEST)

    try:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.REDIRECT_URI,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
        }
        
        access_token_url = 'https://oauth2.googleapis.com/token'
        response = requests.post(access_token_url, data=data)
        user_data = response.json()
        
        if 'error' in user_data:
            return Response({"error": user_data.get('error_description', user_data['error'])}, status=status.HTTP_400_BAD_REQUEST)

    except requests.exceptions.RequestException as e:
        return Response({"error": f"Error getting access token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
    user_info_response = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo', 
        headers={
        'Authorization': f'Bearer {user_data['access_token']}'
    })

    if user_info_response.status_code != 200:
        return Response(f"Error getting user info: {user_info_response.text}", status=status.HTTP_400_BAD_REQUEST)
    
    user_info = user_info_response.json()

    data = {
        'email': user_info['email'],
        'google_access_token': user_data['access_token'],
    }

    save_user_data = save_user(data)
    save_user_data['user']['google_refresh_token'] = user_data['refresh_token']

    return Response(save_user_data, status=status.HTTP_200_OK)

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
            logout(user)
            return Response({'Detail': 'Login expired. Please sign in again.'}, status=status.HTTP_401_UNAUTHORIZED)
        elif token_info.get('error'):
            return Response({'Detail': f"Error during new access token process: {token_info['error_description']}"}, status=status.HTTP_400_BAD_REQUEST)

        user.access_token = token_info['access_token']
        user.access_token_expires_at = datetime.now(dt_timezone.utc) + timedelta(seconds=token_info['expires_in'])
        user.save()

        return token_info['access_token']
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
            return Response(generate_jwt_neuroprof(user), status=status.HTTP_200_OK)

        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': 'User with this email already exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        create_kwargs = {'email': email, 'password': password}
        user = User.objects.create_user(**create_kwargs)
        return Response(generate_jwt_neuroprof(user), status=status.HTTP_201_CREATED)