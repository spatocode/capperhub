import pytz
from datetime import datetime, timedelta
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from core.tests.view_test_mixins import get_mock_request
from core.views.core import UserSubscriptionView
from core.models.user import UserAccount
from core.models.subscription import Subscription


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache" }})
class PuntersViewTest(APITestCase):
    fixtures = ['useraccount.json', 'users.json', 'currency.json', 'pricing.json', 'wallet.json', 'subscription.json', 'transaction.json']

    def test_view_get_punters(self):
        url = reverse('punters')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache" }})
class UserSubscriptionViewTest(APITestCase):
    fixtures = ['useraccount.json', 'users.json', 'currency.json', 'pricing.json', 'wallet.json', 'subscription.json', 'transaction.json']

    def setUp(self):
        self.user_jwt = b'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjZDMwODg5MS04ZGNiLTQ4MmUtYjEyYS1kZmE3MWMzMjhlNWMiLCJ1c2VybmFtZSI6ImRlbW9fc2xAY29oZXJlbnQuY29tLmhrIiwiZW1haWwiOiJkZW1vX3NsQGNvaGVyZW50LmNvbS5oayIsImdyb3VwcyI6WyJ1c2VyOnB1bHNlLnNlYXNvbmFsaWZlLnRlc3RpbmciXSwiaWF0IjoxNTc2MDU2MjY3LCJleHAiOjE1NzcxNTg2OTgsImp0aSI6IjVlODcwYzMwLTY5NzItNDI5MS05ZmJmLTc0MzI1YjBmMTczMCJ9.GujoCXMBhDzuEp16lVdZtDoXoasJW4w4pM1gBXODTNw'
        self.test_format = 'json'

    def test_get_object(self):
        useraccount = UserAccount.objects.get(id=3)
        request = get_mock_request(useraccount.user)
        self.client.force_authenticate(user=useraccount.user)
        view = UserSubscriptionView()
        view.request = request
        actual = view.get_object(3)
        self.assertEqual(actual, useraccount)
    
    def test_view_get_subscriptions(self):
        useraccount = UserAccount.objects.get(id=1)
        url = reverse('user-subscriptions')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json()[0]['id'], 125)

    def test_view_get_subscribers(self):
        useraccount = UserAccount.objects.get(id=9)
        url = reverse('user-subscribers')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json()[0]['id'], 129)
    
    def test_view_get_transactions(self):
        useraccount = UserAccount.objects.get(id=98)
        url = reverse('transactions')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json()[0]['id'], 51)
    
    def test_view_subscribe_users(self):
        data = {
            "type": 1,
            "tipster": 1,
            "amount": 5000,
            "period": 30
        }
        useraccount = UserAccount.objects.get(id=98)
        url = reverse('subscribe-user')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.post(url, data, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json()['data']['issuer']['id'], 1)

    def test_view_unsubscribe_users(self):
        data = {
            "type": 1,
            "tipster": 9,
        }
        useraccount = UserAccount.objects.get(id=98)
        url = reverse('unsubscribe-user')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.post(url, data, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json()['data']['issuer']['id'], 9)


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache" }})
class PlayViewTest(APITestCase):
    fixtures = [
        'useraccount.json',
        'users.json',
        'currency.json',
        'pricing.json',
        'wallet.json',
        'subscription.json',
        'play.json',
        'playslip.json',
    ]

    def setUp(self):
        self.user_jwt = b'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjZDMwODg5MS04ZGNiLTQ4MmUtYjEyYS1kZmE3MWMzMjhlNWMiLCJ1c2VybmFtZSI6ImRlbW9fc2xAY29oZXJlbnQuY29tLmhrIiwiZW1haWwiOiJkZW1vX3NsQGNvaGVyZW50LmNvbS5oayIsImdyb3VwcyI6WyJ1c2VyOnB1bHNlLnNlYXNvbmFsaWZlLnRlc3RpbmciXSwiaWF0IjoxNTc2MDU2MjY3LCJleHAiOjE1NzcxNTg2OTgsImp0aSI6IjVlODcwYzMwLTY5NzItNDI5MS05ZmJmLTc0MzI1YjBmMTczMCJ9.GujoCXMBhDzuEp16lVdZtDoXoasJW4w4pM1gBXODTNw'
        self.test_format = 'json'
    
    def test_only_subscriber_can_view_play(self):
        useraccount = UserAccount.objects.get(id=98)
        url = reverse('plays')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(len(response.json()), 5)

    def test_non_subscriber_cannot_view_play(self):
        subscription = Subscription.objects.get(
            type=1,
            subscriber=98,
            issuer=9,
            is_active=True
        )
        subscription.is_active = False
        subscription.save()
        useraccount = UserAccount.objects.get(id=98)
        url = reverse('plays')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(len(response.json()), 1)

    def test_free_subscriber_cannot_view_premium_play(self):
        useraccount = UserAccount.objects.get(id=1)
        url = reverse('plays')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.get(url, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(len(response.json()), 4)

    def test_create_new_play(self):
        data = {
            "issuer": 98,
            "title": "test-title",
            "is_premium": True,
            "date_added": datetime.utcnow().replace(tzinfo=pytz.UTC),
            "plays": [{
                "match_day": datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=10),
                "sports": "Soccer",
                "competition": "La Liga",
                "home_team": "Levante",
                "away_team": "Malaga",
                "prediction": "Draw",
            }]
        }
        useraccount = UserAccount.objects.get(id=98)
        url = reverse('plays')
        self.client.force_authenticate(user=useraccount.user, token=self.user_jwt)
        response = self.client.post(url, data, format=self.test_format)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.json()['data']['issuer']['id'], 98)
