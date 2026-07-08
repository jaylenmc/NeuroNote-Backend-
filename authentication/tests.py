from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from neuro_profile.models import PinnedResourcesDashboard
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from neuro_profile.models import NeuroProfile
import jwt
from unittest.mock import MagicMock
from authentication.services import verify_google_id_token

class AuthUserTests(APITestCase):
    @patch('authentication.services.PyJWKClient')
    @patch('authentication.services.jwt.decode')
    @patch('authentication.views.requests.post')
    def test_google_api(self, mock_post, mock_decode, mock_PyJWKClient):
        print('==================== Google Api ====================')
        url = reverse('google-api')

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'id_token': 'test_id_token',
            'expires_in': 3600,
            'token_type': 'Bearer',
            'scope': 'email profile openid',
        }

        signing_key = MagicMock(key='test-key')
        mock_PyJWKClient.return_value.get_signing_key_from_jwt.return_value = signing_key
        mock_decode.return_value = {
            'email': 'john@gmail.com',
            'iss': 'https://accounts.google.com',
        }

        data = {'code': 'test_code', 'state': 'test-state'}
        self.client.cookies['oauth_state'] = 'test-state'
        response = self.client.get(url, data)

        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code,
            msg=f"Status code error: {response.data}"
        )

        self.assertEqual(
            response.data['user']['email'],
            'john@gmail.com',
            msg=f"User email error: {response.data['user']['email']}"
        )
        self.assertIn('username', response.data['user'])
        self.assertIn('jwt_data', response.data)
        self.assertNotIn('google_refresh_token', response.data['user'])

class CustomUserTest(APITestCase):
    def test_neuro_create_user_login_correct_credentials(self):
        url = reverse('neuro-create-user')
        User = get_user_model()

        login_data = {
            'email': 'existinguser@gmail.com',
            'password': 'gibberish',
        }
        User.objects.create_user(**login_data)

        response = self.client.post(f"{url}?type=login", data=login_data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Error -> {response.data}",
        )
        self.assertEqual(
            response.data['user']['email'],
            login_data['email'],
            msg=f"User email error: {response.data}",
        )
        self.assertIn('jwt_data', response.data)
        self.assertIn(('access'), response.data['jwt_data'])
        self.assertIn('refresh', response.data['jwt_data'])

    def test_neuro_create_user_login_incorrect_email(self):
        url = reverse('neuro-create-user')
        User = get_user_model()

        login_data = {
            'email': 'incorrectuser@gmail.com',
            'password': 'gibberish',
        }
        response = self.client.post(f"{url}?type=login", data=login_data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            msg=f"Error -> {response.data}",
        )

    def test_neuro_create_user_login_incorrect_password(self):
        url = reverse('neuro-create-user')
        User = get_user_model()

        login_data = {
            'email': 'existinguser@gmail.com',
            'password': 'validpassword',
        }
        User.objects.create_user(**login_data)
        login_data['password'] = 'invalidpassword'

        response = self.client.post(f"{url}?type=login", data=login_data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            msg=f"Error -> {response.data}",
        )

    def test_neuro_create_user_signup_email_exists(self):
        url = reverse('neuro-create-user')
        User = get_user_model()

        login_data = {
            'email': 'existinguser@gmail.com',
            'password': 'gibberish',
        }
        User.objects.create_user(**login_data)

        response = self.client.post(
            f'{url}?type=signup', data=login_data, format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
            msg=f"Error -> {response.data}",
        )
    
    def test_neuro_create_user_signup_incorrect_email(self):
        url = reverse('neuro-create-user')
        User = get_user_model()

        login_data = {
            'email': 'incorrectusergmail.com',
            'password': 'gibberish',
        }
        response = self.client.post(f"{url}?type=signup", data=login_data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {response.data}",
        )
    
    def test_neuro_create_user_signup_incorrect_password(self):
        url = reverse('neuro-create-user')
        User = get_user_model()

        login_data = {
            'email': 'newuser@gmail.com',
            'password': 'gibberishfesufbef4839394893',
        }
        response = self.client.post(f"{url}?type=signup", data=login_data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {response.data}",
        )