from django.contrib.auth.models import User
from django.db import models
from django_countries.fields import CountryField

class Price(models.Model):
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, null=True)
    currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE, null=True)
    amount = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now=True)

class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_tipster = models.BooleanField(default=False)
    country = CountryField()
    phone_number = models.IntegerField(null=True, unique=True)
    email_verified = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f'{self.user.username}'
