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
from authentication.services import authenticate_google_user

class AuthUserTests(APITestCase):
    @patch('authentication.views.authenticate_google_user')
    @patch('authentication.views.requests.post')
    def test_google_api(self, mock_post, mock_authenticate):
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

        mock_authenticate.return_value = {
            'user': {
                'email': 'john@gmail.com',
                'username': 'john',
                'google_access_token': 'test_access_token',
            },
            'jwt_data': 'test_jwt_data',
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
        self.assertIn('google_refresh_token', response.data['user'])
        mock_authenticate.assert_called_once_with('test_id_token', 'test_access_token')

        print(f'Response Data: {response.data}')

    @patch('authentication.views.requests.post')
    def test_google_api_state_mismatch(self, mock_post):
        url = reverse('google-api')
        self.client.cookies['oauth_state'] = 'stored-state'
        response = self.client.get(url, {'code': 'test_code', 'state': 'different-state'})

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            msg=f"Error -> {response.data}",
        )
        mock_post.assert_not_called()

    @patch('authentication.services.verify_google_id_token', return_value='john@gmail.com')
    def test_authenticate_google_user_creates_new_user(self, mock_verify):
        result = authenticate_google_user('test_id_token', 'test_access_token')

        self.assertEqual(result['user']['email'], 'john@gmail.com')
        self.assertIn('jwt_data', result)
        self.assertTrue(NeuroProfile.objects.filter(user__email='john@gmail.com').exists())
        mock_verify.assert_called_once_with('test_id_token')

    @patch('authentication.services.verify_google_id_token', return_value='existing@gmail.com')
    def test_authenticate_google_user_returns_existing_user(self, mock_verify):
        User = get_user_model()
        existing_user = User.objects.create_user(
            email='existing@gmail.com',
            password='password123',
        )

        result = authenticate_google_user('test_id_token', 'test_access_token')

        self.assertEqual(result['user']['email'], existing_user.email)
        self.assertEqual(User.objects.filter(email='existing@gmail.com').count(), 1)
        mock_verify.assert_called_once_with('test_id_token')

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
            status.HTTP_201_CREATED,
            msg=f"Error -> {correct_response.data}"
        )
        self.assertEqual(correct_response.data['user']['email'], correct_data['email'])
        self.assertIn("username", correct_response.data['user'])
        self.assertIn('jwt_data', correct_response.data)
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
        self.assertIn('jwt_data', response.data)
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
