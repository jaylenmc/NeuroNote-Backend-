from rest_framework.test import APITestCase
from .models import AuthUser
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

class AuthUserTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = AuthUser.objects.create_user(
            email='test@gmail.com',
            password='12345',
        )
        refresh = RefreshToken.for_user(user=cls.user)
        refresh['email'] = cls.user.email
        cls.user.refresh_token = str(refresh)
        cls.user.jwt_token = str(refresh.access_token)
        cls.url = reverse('jwt-refresh')
        print(f'Refresh Token: {str(refresh)}')

    def setUp(self):
        ...

    @patch('authentication.views.requests.post')
    def test_token_refresh(self, mock_post):
        print('==================== Refresh Token ====================')
        # Test refresh token from cookies (production)
        # self.client.cookies['refresh_token'] = self.user.refresh_token

        response = self.client.post(self.url, data={'refresh_token': self.user.refresh_token}, format='json')

        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code,
            msg=f"status code error: {response.data}"
        )
        
        print(f"Response data: {response.data}")

    @patch('authentication.views.requests.get')
    @patch('authentication.views.requests.post')
    def test_google_api(self, mock_post, mock_get):
        print('==================== Google Api ====================')
        url = reverse('google-api')

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600,
            'token_type': 'Bearer',
            'scope': 'email profile openid',
            'id_token': 'test_id_token',
        }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'email': 'test@gmail.com',
            'sub': '1234567890',
            'name': 'Test User'
        }

        data = {'code': 'test_code'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(
            status.HTTP_200_OK, 
            response.status_code,
            msg=f"Status code error: {response.data}"
            )
        print(f'Response Data: {response.data}')