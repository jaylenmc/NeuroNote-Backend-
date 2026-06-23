from django.conf import settings
import jwt
from jwt import PyJWKClient
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import GoogleAuthUserModelSerializer, AuthUserModelSerializer
from neuro_profile.models import NeuroProfile
from neuro_profile.models import PinnedResourcesDashboard
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

def save_user(user: dict | User) -> dict:
    if isinstance(user, User):
        user_obj = user
        user_data = GoogleAuthUserModelSerializer(user_obj).data
    else:
        user_serializer = GoogleAuthUserModelSerializer(data=user, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_obj = user_serializer.save()
        user_data = user_serializer.data

    jwt_token_info = RefreshToken.for_user(user_obj).access_token
    save_neuro_profile(user_obj, str(jwt_token_info))

    return {'user': user_data, 'jwt_data': str(jwt_token_info)}

def verify_google_id_token(id_token: str) -> str:
    jwks_client = PyJWKClient("https://www.googleapis.com/oauth2/v3/certs")
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)
    payload = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=['RS256'],
        audience=settings.GOOGLE_CLIENT_ID,
    )

    google_oidc_issuers = ('https://accounts.google.com', 'accounts.google.com')

    if payload.get('iss') not in google_oidc_issuers:
        raise jwt.InvalidIssuerError('Invalid token issuer.')

    email = payload.get('email')
    if not email:
        raise jwt.InvalidTokenError('Email claim missing from id token.')

    return email

def authenticate_google_user(id_token: str, google_access_token: str) -> dict:
    email = verify_google_id_token(id_token)
    user = User.objects.filter(email=email).first()

    if user:
        return save_user(user)

    return save_user({
        'email': email,
        'google_access_token': google_access_token,
    })