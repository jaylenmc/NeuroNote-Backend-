from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from neuro_profile.models import NeuroProfile

class AuthUserTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create_user(
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
        self.assertTrue(
            NeuroProfile.objects.filter(user=self.user).exists(),
            msg=f"NeuroProfile not created: {response.data}"
            )
        print(f'Response Data: {response.data}')

class CustomUserTest(APITestCase):
    def test_custom_user_model(self):
        url = reverse('neuro-create-user')

        correct_data = {
            'email': "johndoe05@gmail.com",
            'password': "gibberish"
        }

        missing_pw_data = {
            'email': "johnddsfoesd05@gmail.com"
        }

        faulty_email_data = {
            'email': 'jamal93gmail.com',
            'password': "gibberish"
        }
        
        correct_response = self.client.post(url, data=correct_data, format='json')
        self.assertEqual(
            correct_response.status_code,
            status.HTTP_200_OK,
            msg=f"Error -> {correct_response.data}"
        )
        self.assertIn('username', correct_response.data)
        self.assertIn('email', correct_response.data)
        self.assertEqual(correct_response.data['email'], correct_data['email'])
        self.assertNotIn('password', correct_response.data)

        missing_pw_response = self.client.post(url, data=missing_pw_data, format='json')
        self.assertEqual(
            missing_pw_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {missing_pw_response.data}"
        )

        faulty_email_response = self.client.post(url, data=faulty_email_data, format='json')
        self.assertEqual(
            faulty_email_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {faulty_email_response.data}"
        )
        
