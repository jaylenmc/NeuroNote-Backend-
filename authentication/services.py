from django.conf import settings
import jwt
from jwt import PyJWKClient
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import GoogleAuthUserModelSerializer, AuthUserModelSerializer
from neuro_profile.models import NeuroProfile
from neuro_profile.models import PinnedResourcesDashboard
from .models import User

def save_neuro_profile(user: User):
    neuro_profile = NeuroProfile.objects.filter(user=user)
    if not neuro_profile.exists():
        neuro_profile = NeuroProfile.objects.create(user=user)
    else:
        neuro_profile = neuro_profile.first()
        print(neuro_profile)

    if not PinnedResourcesDashboard.objects.filter(user=neuro_profile).exists():
        PinnedResourcesDashboard.objects.create(user=neuro_profile)

def save_user(user: dict, auth_provider: str) -> dict:
    if auth_provider == 'password':
        user_data_serializer = AuthUserModelSerializer(data=user)
    elif auth_provider == 'google':
        user_data_serializer = GoogleAuthUserModelSerializer(data=user)
    else:
        raise ValueError(f'Invalid auth provider: {auth_provider}')
    
    user_data_serializer.is_valid(raise_exception=True)
    user_obj = user_data_serializer.save()

    jwt_token_info = RefreshToken.for_user(user_obj)
    save_neuro_profile(user_obj)

    return {'user': user_data_serializer.data, 'jwt_data': {
        'access': str(jwt_token_info.access_token),
        'refresh': str(jwt_token_info),
    }}

def verify_google_id_token(id_token: str) -> dict:
    try:
        jwks_client = PyJWKClient('https://www.googleapis.com/oauth2/v3/certs')
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=['RS256'],
            audience=settings.GOOGLE_CLIENT_ID,
            issuer='https://accounts.google.com',
        )
    except jwt.PyJWTError as exc:
        raise jwt.InvalidTokenError('Invalid Google token') from exc

    email = payload.get('email')
    if not email:
        raise jwt.InvalidTokenError('Email claim missing from id token.')

    return save_user({'email': email}, auth_provider='google')