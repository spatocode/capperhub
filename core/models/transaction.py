from django.core.validators import RegexValidator
from django.db import models
from django_countries.fields import CountryField
from core.shared.model_utils import generate_reference_code

class Currency(models.Model):
    code_validator = RegexValidator(
        regex='[A-Z]{3}',
        message='Please enter a valid 3-letter currency code'
    )
    code = models.CharField(max_length=3, primary_key=True, validators=[code_validator])
    country = CountryField()

    def __str__(self):
        return f'{self.code}'


class Transaction(models.Model):
    PAYSTACK = 0
    FLUTTERWAVE = 1
    PAYPAL = 2
    FAILED = 0
    SUCCEED = 1
    PENDING = 2
    TRANSACTION_STATUS = (
        (FAILED, 'FAILED'),
        (SUCCEED, 'SUCCEED'),
        (PENDING, 'PENDING'),
    )
    PAYMENT_ISSUER = (
        (PAYSTACK, 'PAYSTACK'),
        (FLUTTERWAVE, 'FLUTTERWAVE'),
        (PAYPAL, 'PAYPAL'),
    )
    amount = models.IntegerField(default=0, editable=False)
    reference = models.CharField(max_length=32, default=generate_reference_code, editable=False)
    status = models.PositiveIntegerField(choices=TRANSACTION_STATUS, editable=False)
    user = models.ForeignKey('core.UserAccount', on_delete=models.PROTECT, related_name='user_transaction', editable=False)
    currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE, related_name='currency_transaction', editable=False)
    time = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)
