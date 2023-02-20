import pytz
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django_countries.fields import CountryField
from .subscription import Subscription


class Wallet(models.Model):
    balance = models.FloatField(default=0.00)
    bank = models.CharField(max_length=40)
    account_number = models.IntegerField()


class Pricing(models.Model):
    amount = models.IntegerField(default=0)
    percentage_discount = models.DecimalField(default=0.0, max_digits=19, decimal_places=10)
    date = models.DateTimeField(auto_now=True)
    free_features = ArrayField(models.CharField(max_length=50), blank=True)
    premium_features = ArrayField(models.CharField(max_length=50), blank=True)

    def __str__(self):
        return f'{self.amount}'


class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(null=True, max_length=50)
    bio = models.TextField(null=True)
    country = CountryField(null=True)
    phone_number = models.CharField(null=True, unique=True, max_length=22)
    email_verified = models.BooleanField(default=False)
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, null=True)
    pricing = models.ForeignKey('core.Pricing', on_delete=models.PROTECT, null=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, null=True, related_name='wallet_owner')
    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f'{self.user.username}'

    @property
    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'

    @property
    def is_tipster(self):
        active_plays = self.play_set.filter(match_day__lt=datetime.utcnow().replace(tzinfo=pytz.UTC))
        if active_plays.count() > 0:
            return True
        return False

    # TODO: To minimize access to DB, consider removing these count properties and use 
    # the data returned in other properties to get count
    @property
    def subscriber_count(self):
        num_of_subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True,
        ).distinct('subscriber').count()
        return num_of_subscribers
    
    @property
    def subscription_count(self):
        num_of_subscriptions = Subscription.objects.filter(
            subscriber=self.pk,
            is_active=True,
        ).distinct('subscriber').count()
        return num_of_subscriptions

    @property
    def subscribers(self):
        subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True
        )
        return subscribers
    
    @property
    def subscribers(self):
        subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True
        )
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
