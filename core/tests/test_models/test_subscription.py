from django.test import TestCase
from django.contrib.auth.models import User
from core.models.subscription import Subscription


class SubscriptionModelTestCase(TestCase):
    fixtures = ['useraccount.json', 'users.json', 'pricing.json', 'currency.json', 'wallet.json', 'subscription.json']

    def test_type_label(self):
        subscription = Subscription.objects.get(id=105)
        field_label = subscription._meta.get_field("type").verbose_name
        self.assertEqual(field_label, "type")

    def test_issuer_label(self):
        subscription = Subscription.objects.get(id=105)
        field_label = subscription._meta.get_field("issuer").verbose_name
        self.assertEqual(field_label, "issuer")

    def test_subscriber_label(self):
        subscription = Subscription.objects.get(id=105)
        field_label = subscription._meta.get_field("subscriber").verbose_name
        self.assertEqual(field_label, "subscriber")

    def test_period_label(self):
        subscription = Subscription.objects.get(id=105)
        field_label = subscription._meta.get_field("period").verbose_name
        self.assertEqual(field_label, "period")

    def test_subscription_date_label(self):
        subscription = Subscription.objects.get(id=105)
        field_label = subscription._meta.get_field("subscription_date").verbose_name
        self.assertEqual(field_label, "subscription date")

    def test_expiration_date_label(self):
        subscription = Subscription.objects.get(id=105)
        field_label = subscription._meta.get_field("expiration_date").verbose_name
        self.assertEqual(field_label, "expiration date")

    def test_is_active_label(self):
        subscription = Subscription.objects.get(id=105)
        field_label = subscription._meta.get_field("is_active").verbose_name
        self.assertEqual(field_label, "is active")

    def test__str__label(self):
        subscription = Subscription.objects.get(id=105)
        self.assertEqual(subscription.__str__(), f"{subscription.type}-{subscription.issuer.user.username}->{subscription.subscriber.user.username}")
