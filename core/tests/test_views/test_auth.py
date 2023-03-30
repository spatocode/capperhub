from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache" }})
class UserRegisterationViewTest(APITestCase):
    fixtures = ['currency.json']

    def setUp(self):
        self.API_URL = 'account_signup'
        self.test_format = 'json'
        self.expected_data = {'detail': 'Verification e-mail sent.'}

    def test_view_url_exists_at_desired_location(self):
        data = {
            "country": "US",
            "email": "user@email.com",
            "display_name": "Memphis Depay",
            "password1": "0987654gh",
            "password2": "0987654gh"
        }
        url = reverse(self.API_URL)
        response = self.client.post(url, data, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json(), self.expected_data)
