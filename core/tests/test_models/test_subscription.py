from django.test import TestCase
from django.contrib.auth.models import User
from core.models.subscription import Subscription


class SubscriptionModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        issuer = User.objects.create(username="johndoe3", password="password3")
        subscriber = User.objects.create(username="johndoe4", password="password4")
        Subscription.objects.create(
            type=Subscription.FREE,
            issuer=issuer.useraccount,
            subscriber=subscriber.useraccount,
        )

    def test_type_label(self):
        subscription = Subscription.objects.get(id=1)
        field_label = subscription._meta.get_field("type").verbose_name
        self.assertEqual(field_label, "type")

    def test_issuer_label(self):
        subscription = Subscription.objects.get(id=1)
        field_label = subscription._meta.get_field("issuer").verbose_name
        self.assertEqual(field_label, "issuer")

    def test_subscriber_label(self):
        subscription = Subscription.objects.get(id=1)
        field_label = subscription._meta.get_field("subscriber").verbose_name
        self.assertEqual(field_label, "subscriber")

    def test_period_label(self):
        subscription = Subscription.objects.get(id=1)
        field_label = subscription._meta.get_field("period").verbose_name
        self.assertEqual(field_label, "period")

    def test_subscription_date_label(self):
        subscription = Subscription.objects.get(id=1)
        field_label = subscription._meta.get_field("subscription_date").verbose_name
        self.assertEqual(field_label, "subscription date")

    def test_expiration_date_label(self):
        subscription = Subscription.objects.get(id=1)
        field_label = subscription._meta.get_field("expiration_date").verbose_name
        self.assertEqual(field_label, "expiration date")

    def test_is_active_label(self):
        subscription = Subscription.objects.get(id=1)
        field_label = subscription._meta.get_field("is_active").verbose_name
        self.assertEqual(field_label, "is active")

    def test__str__label(self):
        subscription = Subscription.objects.get(id=1)
        self.assertEqual(subscription.__str__(), f"{subscription.type}-{subscription.issuer.user.username}->{subscription.subscriber.user.username}")
