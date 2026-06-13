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

class AuthUserTests(APITestCase):
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
            'email': "john@gmail.com",
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

        self.assertEqual(
            response.data['user']['email'],
            'john@gmail.com',
            msg=f"User email error: {response.data['user']['email']}"
        )
        self.assertIn('username', response.data['user'])
        self.assertIn('jwt_data', response.data)
        self.assertNotIn('password', response.data['user'])
        self.assertTrue(NeuroProfile.objects.filter(user__email='john@gmail.com').exists())
        self.assertTrue(PinnedResourcesDashboard.objects.filter(user__user__email='john@gmail.com').exists())

        print(f'Response Data: {response.data}')

class CustomUserTest(APITestCase):
    def test_neuro_create_user_signin(self):
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

        missing_type_response = self.client.post(url, data=correct_data, format='json')
        self.assertEqual(
            missing_type_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {missing_type_response.data}",
        )

        correct_response = self.client.post(
            f'{url}?type=signin', data=correct_data, format='json'
        )
        self.assertEqual(
            correct_response.status_code,
            status.HTTP_200_OK,
            msg=f"Error -> {correct_response.data}"
        )
        self.assertEqual(correct_response.data['user']['email'], correct_data['email'])
        self.assertIn("username", correct_response.data['user'])
        self.assertIn('jwt_refresh', correct_response.data)
        self.assertNotIn('password', correct_response.data)

        duplicate_response = self.client.post(
            f'{url}?type=signin', data=correct_data, format='json'
        )
        self.assertEqual(
            duplicate_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {duplicate_response.data}",
        )

        missing_pw_response = self.client.post(
            f'{url}?type=signin', data=missing_pw_data, format='json'
        )
        self.assertEqual(
            missing_pw_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {missing_pw_response.data}"
        )

        faulty_email_response = self.client.post(
            f'{url}?type=signin', data=faulty_email_data, format='json'
        )
        self.assertEqual(
            faulty_email_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {faulty_email_response.data}"
        )

        print('==================== Signin Correct Data ====================')
        print(f'Response Data: {correct_response.data}\n')
        print('=========================Missing Pw==============================')
        print(f'Response Data: {missing_pw_response.data}\n')
        print('=========================Faulty Email==============================')
        print(f'Response Data: {faulty_email_response.data}')

    def test_neuro_create_user_login_post(self):
        url = reverse('neuro-create-user')
        User = get_user_model()

        login_data = {
            'email': 'existinguser@gmail.com',
            'password': 'gibberish',
        }
        User.objects.create_user(**login_data)

        response = self.client.post(
            f'{url}?type=login', data=login_data, format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Error -> {response.data}",
        )
        self.assertEqual(response.data['user']['email'], login_data['email'])
        self.assertIn('id', response.data['user'])
        self.assertIn('username', response.data['user'])
        self.assertIn('jwt_refresh', response.data)
        self.assertEqual(
            NeuroProfile.objects.filter(user__email=login_data['email']).count(),
            1,
        )

        wrong_password_response = self.client.post(
            f'{url}?type=login',
            data={'email': login_data['email'], 'password': 'wrongpassword'},
            format='json',
        )
        self.assertEqual(
            wrong_password_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            msg=f"Error -> {wrong_password_response.data}",
        )

        missing_user_response = self.client.post(
            f'{url}?type=login',
            data={'email': 'nobody@gmail.com', 'password': 'gibberish'},
            format='json',
        )
        self.assertEqual(
            missing_user_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            msg=f"Error -> {missing_user_response.data}",
        )

        missing_body_response = self.client.post(
            f'{url}?type=login',
            data={'email': login_data['email']},
            format='json',
        )
        self.assertEqual(
            missing_body_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Error -> {missing_body_response.data}",
        )
