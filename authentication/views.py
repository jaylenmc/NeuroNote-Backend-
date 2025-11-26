from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
import requests
from django.conf import settings
from .models import AuthUser
from .serializers import UserSerializer
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo
from django.contrib.auth import logout
from rest_framework import status
from achievements.models import UserAchievements, Achievements
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from solostudyroom.models import PinnedResourcesDashboard
from django.http import JsonResponse

def ping(request):
    return JsonResponse({'message': 'OK'}, status=status.HTTP_200_OK)

@api_view(['OPTIONS'])
@permission_classes([AllowAny])
def options_test(request):
    return Response({"ok": True}, status=200)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def googleApi(request):
    # Handle OPTIONS preflight requests
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    print("Origin:", request.headers.get("Origin"))
    code = request.data.get('code')
    error = request.data.get('error')
    print(f"code: {code}")
    print(f"error: {error}")

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
        response = requests.post(access_token_url, data=data, timeout=5)
        print(f"response: {response.json()}")
        user_data = response.json()
        
        if 'error' in user_data:
            return Response({"error": user_data.get('error_description', user_data['error'])}, status=status.HTTP_400_BAD_REQUEST)
        
        user_access_token = user_data.get('access_token')
        user_expires_in = datetime.now(dt_timezone.utc) + timedelta(seconds=user_data.get('expires_in'))
        user_refresh_token = user_data.get('refresh_token')

    except requests.exceptions.RequestException as e:
        return Response({"error": f"Error getting access token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
    header = {
        'Authorization': f'Bearer {user_access_token}'
    }
    user_info_response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=header, timeout=5)

    if user_info_response.status_code != 200:
        return Response(f"Error getting user info: {user_info_response.text}", status=status.HTTP_400_BAD_REQUEST)
    
    user_info = user_info_response.json()
    email = user_info.get('email')

    user = AuthUser.objects.filter(email=email).first()
    
    if not user:
        user = AuthUser.objects.create_user(
            email=email,
            last_login=timezone.now(),
            google_access_token=user_access_token,
            access_token_expires_at=user_expires_in,
            google_refresh_token=user_refresh_token,
            )
        
    else:
        user.email = email
        user.google_access_token = user_access_token
        user.last_login=timezone.now()
        user.access_token_expires_at = user_expires_in
        if user_refresh_token:
            user.google_refresh_token = user_refresh_token
        user.save()

    # Create pinned resources for user if it doesn't exists
    pinned_resources = PinnedResourcesDashboard.objects.filter(user=user).first()
    if not pinned_resources:
        PinnedResourcesDashboard.objects.create(user=user)

    refresh = RefreshToken.for_user(user)
    refresh['email'] = user.email

    user.jwt_token = str(refresh.access_token)
    user.save()

    # Only the owner can access app (Collecting emails currently)
    if email != "jayzilla195@gmail.com":
        return Response({'Message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    # Assign first login achievement to user
    user_achiev, create = UserAchievements.objects.get_or_create(user=user)
    achievement = Achievements.objects.filter(name="The Journey Begins").first()
    user_achiev.achievements.add(achievement)
    # Update streak
    # if user.last_login_date.day != timezone.now().day:
    #     user.current_streak = 0
    #     user.last_login_date = timezone.now()
    #     user.save()
    # else if user.:
    #     user.current_streak += 1
    #     if user.current_streak > user.longest_streak:
    #         user.longest_streak = user.current_streak
    #     user.save()

    data_serialized = UserSerializer(user)
    
    try:
        if is_token_expired(user):
            access_token = refreshAccessToken(user)
            if isinstance(access_token, Response):
                return access_token
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    response_data = {
        'user': data_serialized.data,
        'jwt_refresh': str(refresh),
    }
    
    response = Response(response_data, status=status.HTTP_200_OK)
    
    # response.set_cookie(
    #     key='refresh_token',
    #     value=str(refresh),
    #     httponly=True,
    #     secure=not settings.DEBUG,
    #     samesite='Lax'
    # )
    
    return response

def is_token_expired(user):
    current_time = datetime.now(dt_timezone.utc)
    refresh_threshold = timedelta(minutes=5)
    return current_time >= (user.access_token_expires_at - refresh_threshold)
        
def refreshAccessToken(user):
    refresh_token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': user.refresh_token,
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
    
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Get from cookies during production
        # refresh_token = request.COOKIES.get('refresh_token')

        # Get from body during development
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'No refresh token found in cookies'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)