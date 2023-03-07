import pytz
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from .subscription import Subscription


def default_free_features():
    return ["Free plays forever"]

def default_premium_features():
    return ["Carefully picked plays"]


class Wallet(models.Model):
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, null=True)
    balance = models.FloatField(default=0.00)
    withheld = models.FloatField(default=0.00)
    bank_name = models.CharField(max_length=50, default="")
    bank_account_number = models.CharField(max_length=50, default="")
    authorizations = ArrayField(models.JSONField(), size=5, null=True)

    def __str__(self) -> str:
        return f'{self.balance} - {self.bank_name}'


class Pricing(models.Model):
    amount = models.IntegerField(default=0)
    percentage_discount = models.DecimalField(default=0.0, max_digits=19, decimal_places=10)
    last_update = models.DateTimeField(auto_now=True)
    free_features = ArrayField(models.CharField(max_length=50), default=default_free_features, size=7, null=True)
    premium_features = ArrayField(models.CharField(max_length=50), default=default_premium_features, size=7, null=True)

    def __str__(self):
        return f'{self.amount}'


class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(default="", max_length=50)
    bio = models.TextField(default="")
    country = CountryField(default="")
    phone_number = models.CharField(null=True, unique=True, max_length=22)
    email_verified = models.BooleanField(default=False)
    pricing = models.ForeignKey('core.Pricing', on_delete=models.PROTECT, null=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, null=True, related_name='wallet_owner')
    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f'{self.user.username}'

    @property
    def full_name(self):
        if not self.user.first_name or not self.user.last_name:
            return ''
        return f'{self.user.first_name} {self.user.last_name}'

    @property
    def is_punter(self):
        try:
            latest_play = self.play_set.latest('date_added')
            if latest_play.date_added + timedelta(days=7) > datetime.utcnow().replace(tzinfo=pytz.UTC):
                return True
            return False
        except:
            return False

    @property
    def subscription_issuers(self):
        subscribers = Subscription.objects.filter(
            subscriber=self.pk,
            is_active=True,
            type=Subscription.FREE
        ).values_list("issuer__user__username", flat=True)
        return subscribers

    @property
    def free_subscribers(self):
        subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True,
            type=Subscription.FREE
        ).values_list("subscriber__user__username", flat=True)
        return subscribers
    
    @property
    def premium_subscribers(self):
        subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True,
            type=Subscription.PREMIUM
        ).values_list("subscriber__user__username", flat=True)
        return subscribers

    def is_subscriber(self, issuer):
        subscriber_count = Subscription.objects.filter(
            issuer=issuer,
            subscriber=self.pk,
            is_active=True,
        ).count()

        if len(subscriber_count) > 0:
            return True
        return False
    
    def is_premium_subscriber(self, issuer):
        subscriber_count = Subscription.objects.filter(
            issuer=issuer,
            subscriber=self.pk,
            type=Subscription.PREMIUM,
            is_active=True,
        ).count()

        if len(subscriber_count) > 0:
            return True
        return False

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserAccount.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.useraccount.save()
