from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse


class TermsOfUseAPITest(APITestCase):
    def test_get(self):
        url = reverse('terms_of_use')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')


class PrivacyPolicyAPITest(APITestCase):
    def test_get(self):
        url = reverse('privacy_policy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')


class FeedbackAPITest(APITestCase):
    data = {
        "email": "test@user.com",
        "message": "A test message"
    }
    def test_get(self):
        url = reverse('feedback')
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')


class WaitlistAPITest(APITestCase):
    data = {
        "email": "test@user.com",
    }
    def test_get(self):
        url = reverse('waitlist')
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
