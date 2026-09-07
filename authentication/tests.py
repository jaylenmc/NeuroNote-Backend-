from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from unittest.mock import MagicMock
from neuro_profile.models import NeuroProfile
from django.core.mail import outbox

class AuthUserTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_email = "john@gmail.com"
    
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
            'email': self.fake_email,
            'iss': 'https://accounts.google.com',
        }

        data = {'code': 'test_code'}
        response = self.client.get(url, data)
        print(response.data)

        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code,
            msg=f"Status code error: {response.data}"
        )

        # self.assertEqual(
        #     response.data['user']["email"],
        #     self.fake_email,
        #     msg=f"User email error: {response.data['user']["email"]}"
        # )
        # self.assertIn('username', response.data['user'])
        # self.assertEqual(response.data["user"]["username"], self.fake_email.split("@")[0])
        # self.assertIn('jwt_data', response.data)
        # user = get_user_model().objects.get(email=self.fake_email)
        # self.assertTrue(NeuroProfile.objects.filter(user=user))
    
    @patch('authentication.services.PyJWKClient')
    @patch('authentication.services.jwt.decode')
    @patch('authentication.views.requests.post')
    def test_google_api_email_in_db(self, mock_post, mock_decode, mock_PyJWKClient):
        print('==================== Google Api Email In DB ====================')
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

        get_user_model().objects.create_user(email=self.fake_email)
        mock_decode.return_value = {
            'email': self.fake_email,
            'iss': 'https://accounts.google.com',
        }

        data = {'code': 'test_code'}
        response = self.client.get(url, data)

        self.assertEqual(
            status.HTTP_200_OK,
            response.status_code,
            msg=f"Status code error: {response.data}"
        )

        self.assertEqual(
            response.data['user']["email"],
            self.fake_email,
            msg=f"User email error: {response.data['user']["email"]}"
        )
        self.assertIn('username', response.data['user'])
        self.assertIn('jwt_data', response.data)
        user = get_user_model().objects.get(email=self.fake_email)
        self.assertTrue(NeuroProfile.objects.filter(user=user))

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
        self.assertIn('Message', response.data)
        self.assertEqual(
            response.data['waitlist'],
            True,
            msg=f"Waitlist error: {response.data}",
        )
        self.assertEqual(
            response.data['Message'],
            'User already in waitlist.',
            msg=f"Message error: {response.data}",
        )

    def test_neuro_create_user_login_incorrect_email(self):
        url = reverse('neuro-create-user')

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
            status.HTTP_200_OK,
            msg=f"Error -> {response.data}",
        )
        self.assertIn('Message', response.data)
        self.assertEqual(
            response.data['waitlist'],
            True,
            msg=f"Waitlist error: {response.data}",
        )
        self.assertEqual(
            response.data['Message'],
            'User already in waitlist.',
            msg=f"Message error: {response.data}",
        )

    def test_neuro_create_user_signup_waitlist_new_user(self):
        url = reverse('neuro-create-user')

        signup_data = {
            'email': 'jaylenmc05@gmail.com',
            'password': 'gibberish',
        }
        response = self.client.post(f"{url}?type=signup", data=signup_data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Error -> {response.data}",
        )
        self.assertIn('Message', response.data)
        self.assertEqual(
            response.data['waitlist'],
            True,
            msg=f"Waitlist error: {response.data}",
        )
        self.assertEqual(
            response.data['Message'],
            'User successfully signed up for waitlist.',
            msg=f"Message error: {response.data}",
        )
        print(outbox)
    
    def test_neuro_create_user_signup_incorrect_email(self):
        url = reverse('neuro-create-user')

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