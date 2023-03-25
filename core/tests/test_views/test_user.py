import pytz
from datetime import datetime
from django.test import override_settings
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
# from rest_framework.test import force_authenticate
# from mock import patch
# from django_fakeredis import FakeRedis, fakeredis

from core.tests.view_test_mixins import get_mock_request
from core.views.user import UserAPIView
from core.models.user import UserAccount


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache" }})
class UserAccountOwnerAPIViewTest(APITestCase):
    fixtures = ['useraccount.json', 'users.json', 'currency.json', 'pricing.json', 'wallet.json']

    def setUp(self):
        self.API_URL = 'account-owner'
        self.user_jwt = b'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjZDMwODg5MS04ZGNiLTQ4MmUtYjEyYS1kZmE3MWMzMjhlNWMiLCJ1c2VybmFtZSI6ImRlbW9fc2xAY29oZXJlbnQuY29tLmhrIiwiZW1haWwiOiJkZW1vX3NsQGNvaGVyZW50LmNvbS5oayIsImdyb3VwcyI6WyJ1c2VyOnB1bHNlLnNlYXNvbmFsaWZlLnRlc3RpbmciXSwiaWF0IjoxNTc2MDU2MjY3LCJleHAiOjE1NzcxNTg2OTgsImp0aSI6IjVlODcwYzMwLTY5NzItNDI5MS05ZmJmLTc0MzI1YjBmMTczMCJ9.GujoCXMBhDzuEp16lVdZtDoXoasJW4w4pM1gBXODTNw'
        self.test_format = 'json'
        self.expected_data = {'id': 3, 'user': {'id': 5, 'last_login': '2023-02-24T17:41:23.283000Z', 'is_superuser': False, 'username': 'chidimokeme', 'first_name': '', 'last_name': '', 'email': 'chidimokeme@gmail.com', 'is_staff': False, 'is_active': True, 'date_joined': '2023-02-24T17:41:22.918000Z', 'groups': [], 'user_permissions': []}, 'pricing': {'id': 15, 'free_features': ['Free plays forever'], 'premium_features': ['Carefully picked plays'], 'amount': 3400.0, 'percentage_discount': '0.0000000000', 'last_update': '2023-03-01T15:55:50.068000Z'}, 'free_subscribers': [], 'premium_subscribers': [], 'subscription_issuers': [], 'full_name': '', 'wallet': {'id': 5, 'balance': 80000.0, 'withheld': 0.0, 'bank_name': 'Union Bank of Nigeria', 'bank_account_number': '0045972721', 'authorizations': [], 'receipent_code': '', 'currency': 'NGN'}, 'country': 'Hungary', 'display_name': 'Chidi Mokeme', 'bio': 'Scar a badass actor', 'phone_number': '+2348074040029', 'twitter_handle': '', 'facebook_handle': '', 'instagram_handle': '', 'ip_address': '127.0.0.1', 'last_updated': '2023-03-21T21:27:38.818322Z'}

    def test_get_object(self):
        useraccount = UserAccount.objects.get(id=3)
        request = get_mock_request(useraccount.user)
        self.client.force_authenticate(user=useraccount.user)
        view = UserAPIView()
        view.request = request
        actual = view.get_object(useraccount.user.username)
        self.assertEqual(actual, useraccount)

    def test_view_url_exists_at_desired_location(self):
        useraccount = UserAccount.objects.get(id=3)
        url = reverse(self.API_URL)
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_view_response_json(self):
        useraccount = UserAccount.objects.get(id=3)
        url = reverse(self.API_URL)
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.json().get('id'), self.expected_data.get('id'))


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache" }})
class UserAPIViewTest(APITestCase):
    fixtures = ['useraccount.json', 'users.json', 'currency.json', 'pricing.json', 'wallet.json']

    def setUp(self):
        self.API_URL = 'users-action'
        self.user_jwt = b'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjZDMwODg5MS04ZGNiLTQ4MmUtYjEyYS1kZmE3MWMzMjhlNWMiLCJ1c2VybmFtZSI6ImRlbW9fc2xAY29oZXJlbnQuY29tLmhrIiwiZW1haWwiOiJkZW1vX3NsQGNvaGVyZW50LmNvbS5oayIsImdyb3VwcyI6WyJ1c2VyOnB1bHNlLnNlYXNvbmFsaWZlLnRlc3RpbmciXSwiaWF0IjoxNTc2MDU2MjY3LCJleHAiOjE1NzcxNTg2OTgsImp0aSI6IjVlODcwYzMwLTY5NzItNDI5MS05ZmJmLTc0MzI1YjBmMTczMCJ9.GujoCXMBhDzuEp16lVdZtDoXoasJW4w4pM1gBXODTNw'
        self.test_format = 'json'
        self.expected_data = {'id': 2, 'user': {'first_name': '', 'last_name': '', 'username': 'yusufdatti', 'email': 'yusufdatti@gmail.com'}, 'pricing': {'id': 16, 'free_features': ['Free plays forever'], 'premium_features': ['Carefully picked plays'], 'amount': 8400.0, 'percentage_discount': '0.0000000000', 'last_update': '2023-03-01T15:56:13.718000Z'}, 'free_subscribers': [], 'premium_subscribers': [], 'subscription_issuers': [], 'country': 'Australia', 'is_punter': False, 'currency': 'NGN', 'display_name': 'Datti Tips', 'bio': '2023 Labour Party Vice Presidential Candidate', 'twitter_handle': '', 'facebook_handle': '', 'instagram_handle': '', 'last_updated': '2023-03-21T21:46:00.783087Z', 'wallet': 6}

    def test_get_object(self):
        useraccount = UserAccount.objects.get(id=3)
        view = UserAPIView()
        actual = view.get_object(useraccount.user.username)
        self.assertEqual(actual, useraccount)

    def test_view_get_url_exists_at_desired_location(self):
        useraccount2 = UserAccount.objects.get(id=2)
        url = reverse(self.API_URL, kwargs={'username': useraccount2.user.username})
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_view_get_response_json(self):
        useraccount2 = UserAccount.objects.get(id=2)
        url = reverse(self.API_URL, kwargs={'username': useraccount2.user.username})
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.json().get('id'), self.expected_data.get('id'))

    def test_view_put_url_exists_at_desired_location(self):
        useraccount = UserAccount.objects.get(id=3)
        data = {
            "country": "US",
            "phone_number": "12345434543",
            "bio": "Testing bio",
            "email": "user@email.com",
            "username": "jong",
            "display_name": "De Jong",
            "twitter": "dejong",
            "facebook": "dejong",
            "instagram": "dejong"
        }
        url = reverse(self.API_URL, kwargs={'username': useraccount.user.username})
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.put(url, data, content_type="multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_view_put_throws_error_when_request_user_is_not_owner_of_the_data(self):
        useraccount = UserAccount.objects.get(id=3)
        useraccount2 = UserAccount.objects.get(id=2)
        data = {
            "country": "US",
            "phone_number": "12345434543",
            "bio": "Testing bio",
            "email": "user@email.com",
            "username": "jong",
            "display_name": "De Jong",
            "twitter": "dejong",
            "facebook": "dejong",
            "instagram": "dejong"
        }
        url = reverse(self.API_URL, kwargs={'username': useraccount2.user.username})
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.put(url, data, content_type="multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response['content-type'], 'application/json')

    def test_view_put_response_json(self):
        useraccount = UserAccount.objects.get(id=3)
        payload = {
            "country": "US",
            "phone_number": "12345434543",
            "bio": "Testing bio",
            "email": "user@email.com",
            "username": "jong",
            "display_name": "De Jong",
            "twitter": "dejong",
            "facebook": "dejong",
            "instagram": "dejong",
            "image": open("core/tests/test.jpg", "rb")
        }
        data = encode_multipart(data=payload, boundary=BOUNDARY)
        url = reverse(self.API_URL, kwargs={'username': useraccount.user.username})
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.put(url, data, content_type=MULTIPART_CONTENT)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json()["data"].get("display_name"), payload.get("display_name"))


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache" }})
class UserPricingAPIViewTest(APITestCase):
    fixtures = ['useraccount.json', 'users.json', 'currency.json', 'pricing.json', 'wallet.json']

    def setUp(self):
        self.API_URL = 'user-pricing'
        self.user_jwt = b'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjZDMwODg5MS04ZGNiLTQ4MmUtYjEyYS1kZmE3MWMzMjhlNWMiLCJ1c2VybmFtZSI6ImRlbW9fc2xAY29oZXJlbnQuY29tLmhrIiwiZW1haWwiOiJkZW1vX3NsQGNvaGVyZW50LmNvbS5oayIsImdyb3VwcyI6WyJ1c2VyOnB1bHNlLnNlYXNvbmFsaWZlLnRlc3RpbmciXSwiaWF0IjoxNTc2MDU2MjY3LCJleHAiOjE1NzcxNTg2OTgsImp0aSI6IjVlODcwYzMwLTY5NzItNDI5MS05ZmJmLTc0MzI1YjBmMTczMCJ9.GujoCXMBhDzuEp16lVdZtDoXoasJW4w4pM1gBXODTNw'
        self.test_format = 'json'

    def test_view_url_exists_at_desired_location(self):
        data = {
            "amount": "1000",
            "percentage_discount": "0.1",
            "free_features": ["just a new free feature"],
            "premium_features": ["just a new premium feature"]
        }
        useraccount = UserAccount.objects.get(id=3)
        url = reverse(self.API_URL)
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.post(url, data, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_view_get_response_json(self):
        data = {
            "amount": "1000.00",
            "percentage_discount": "0.1",
            "free_features": ["just a new free feature"],
            "premium_features": ["just a new premium feature"]
        }
        useraccount = UserAccount.objects.get(id=3)
        url = reverse(self.API_URL)
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.post(url, data, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json()["data"].get("amount"), data.get("amount"))

    def test_view_return_error_when_last_pricing_date_is_not_due(self):
        data = {
            "amount": "1000.00",
            "percentage_discount": "0.1",
            "free_features": ["just a new free feature"],
            "premium_features": ["just a new premium feature"]
        }
        useraccount = UserAccount.objects.get(id=3)
        pricing = useraccount.pricing
        pricing.last_update = datetime.utcnow().replace(tzinfo=pytz.UTC)
        pricing.save()
        url = reverse(self.API_URL)
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.post(url, data, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response['content-type'], 'application/json')
