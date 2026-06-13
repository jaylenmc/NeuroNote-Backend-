from datetime import datetime, timedelta
from django.utils import timezone as dt_timezone
from django.conf import settings
import requests
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth import logout
from .serializers import GoogleAuthUserModelSerializer, AuthUserModelSerializer
from neuro_profile.models import NeuroProfile
from neuro_profile.models import PinnedResourcesDashboard
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

def create_pinned_resources(neuro_profile: NeuroProfile):
    pinned_resources = PinnedResourcesDashboard.objects.filter(user=neuro_profile)
    if not pinned_resources.exists():
        PinnedResourcesDashboard.objects.create(user=neuro_profile)

def save_neuro_profile(user: User, jwt_access_token: str):
    neuro_profile, _ = NeuroProfile.objects.get_or_create(user=user)
    neuro_profile.jwt_token = jwt_access_token
    neuro_profile.save()

    create_pinned_resources(neuro_profile)

def save_user(user: dict | User) -> Response: 
    # Use AuthUserModelSerializer because email and password is required with in app login/signup.
    if isinstance(user, User):
        user_serializer = AuthUserModelSerializer(user)
    else:
        # User GoogleAuthUserModelSerializer because access/refresh tokens are needed to get basic user info.
        user_serializer = GoogleAuthUserModelSerializer(data=user, partial=True)

    user_serializer.is_valid(raise_exception=True)
    user_obj = user_serializer.save()

    jwt_token_info = RefreshToken.for_user(user_obj).access_token

    save_neuro_profile(user_obj, str(jwt_token_info))

    return {'user': user_serializer.data, 'jwt_data': str(jwt_token_info)}