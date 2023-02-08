from django.contrib.auth.models import User
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

    def __str__(self):
        return f'{self.amount}'


class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(null=True, max_length=50)
    bio = models.TextField(null=True)
    is_tipster = models.BooleanField(default=False)
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
    
    # @property
    # def is_complete_profile(self):
    #     if self.user.first_name and self.user.last_name and self.

    @property
    def subscriber_count(self):
        num_of_subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True,
        ).distinct('subscriber').count()
        return num_of_subscribers

    @property
    def subscribers(self):
        subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True
        )
        return subscribers
