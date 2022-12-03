from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User
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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_account')
    is_tipster = models.BooleanField(default=False)
    country = models.CharField(max_length=50, null=True)
    mobile_no = models.IntegerField(null=True)
    subscribers = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='subscribed_account')
    tips = models.ForeignKey(SportsTips, on_delete=models.CASCADE, related_name='tips_owner')
    price = models.IntegerField()
    currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE)
    email_verified = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f'{self.user.username}'
