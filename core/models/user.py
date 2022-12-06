from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from .tips import SportsTips


class Currency(models.Model):
    code_validator = RegexValidator(
        regex='[A-Z]{3}',
        message='Please enter a valid 3-letter currency code'
    )
    code = models.CharField(max_length=3, primary_key=True, validators=[code_validator])

    def __str__(self):
        return f'{self.code}'


class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_tipster = models.BooleanField(default=False)
    country = models.CharField(max_length=50, null=True)
    phone_number = models.IntegerField(null=True, unique=True)
    subscribers = models.ManyToManyField('core.UserAccount', related_name='tipsters')
    tips = models.ForeignKey(SportsTips, on_delete=models.CASCADE, related_name='tips_owner', null=True)
    price = models.IntegerField(default=0)
    currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE, null=True)
    email_verified = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f'{self.user.username}'
