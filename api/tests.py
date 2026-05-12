from django.core import mail
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthApiTests(APITestCase):
    def test_signup_creates_inactive_user_and_sends_otp_email(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'strongpass123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'testuser@example.com')
        self.assertEqual(len(mail.outbox), 1)
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)

    def test_verify_otp_then_login_returns_jwt_tokens(self):
        signup_response = self.client.post(
            reverse('signup'),
            {
                'username': 'loginuser',
                'email': 'loginuser@example.com',
                'password': 'strongpass123',
            },
            format='json',
        )
        self.assertEqual(signup_response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='loginuser')
        otp = user.email_otps.first()
        self.assertIsNotNone(otp)

        blocked_login = self.client.post(
            reverse('login'),
            {'username': 'loginuser', 'password': 'strongpass123'},
            format='json',
        )
        self.assertEqual(blocked_login.status_code, status.HTTP_403_FORBIDDEN)

        verify_response = self.client.post(
            reverse('verify-otp'),
            {'email': 'loginuser@example.com', 'code': otp.code},
            format='json',
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse('login'),
            {'username': 'loginuser', 'password': 'strongpass123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['username'], 'loginuser')
