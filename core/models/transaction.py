from django.core.validators import RegexValidator
from django.db import models
from django_countries.fields import CountryField
from core.shared.model_utils import generate_unique_code

class Currency(models.Model):
    code_validator = RegexValidator(
        regex='[A-Z]{3}',
        message='Please enter a valid 3-letter currency code'
    )
    code = models.CharField(max_length=3, primary_key=True, validators=[code_validator])
    country = CountryField(null=True)

    def __str__(self):
        return f'{self.code}'


class Transaction(models.Model):
    DEPOSIT = 0
    WITHDRAWAL = 1
    PAYSTACK = 0
    FAILED = 0
    SUCCEED = 1
    PENDING = 2
    TRANSACTION_STATUS = (
        (FAILED, 'FAILED'),
        (SUCCEED, 'SUCCEED'),
        (PENDING, 'PENDING'),
    )
    TRANSACTION_TYPE = (
        (DEPOSIT, 'DEPOSIT'),
        (WITHDRAWAL, 'WITHDRAWAL')
    )
    PAYMENT_ISSUER = (
        (PAYSTACK, 'PAYSTACK'),
    )
    type = models.PositiveIntegerField(choices=TRANSACTION_TYPE, editable=False)
    amount = models.IntegerField(default=0, editable=False)
    balance = models.IntegerField(default=0, editable=False)
    reference = models.CharField(max_length=32, default=generate_unique_code, editable=False)
    payment_issuer = models.PositiveIntegerField(choices=PAYMENT_ISSUER, editable=False)
    channel = models.CharField(max_length=100, editable=False)
    status = models.PositiveIntegerField(choices=TRANSACTION_STATUS, editable=False)
    user = models.ForeignKey('core.UserAccount', on_delete=models.PROTECT, related_name='user_transactions', editable=False)
    currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE, related_name='currency_transaction', editable=False)
    time = models.DateTimeField(auto_now=True, editable=False)
