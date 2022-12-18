from django.contrib.auth.models import User
from django.db import models
from django_countries.fields import CountryField

class Pricing(models.Model):
    amount = models.IntegerField(default=0)
    percentage_discount = models.DecimalField(default=0.0, max_digits=19, decimal_places=10)
    date = models.DateTimeField(auto_now=True)
    trial_period = models.PositiveIntegerField(default=14)

    def __str__(self):
        return f'{self.amount}'


class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(null=True)
    is_tipster = models.BooleanField(default=False)
    country = CountryField(null=True)
    phone_number = models.CharField(null=True, unique=True, max_length=22)
    email_verified = models.BooleanField(default=False)
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT, null=True)
    pricing = models.ForeignKey('core.Pricing', on_delete=models.PROTECT, null=True)
    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f'{self.user.username}'
