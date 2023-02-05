from django.db import models
from django.utils.timezone import now
from core.shared.model_utils import generate_unique_code

class Payment(models.Model):
    base_price = models.IntegerField(default=0)
    base_currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE, null=True, related_name='base_currency_payment')
    payment_price = models.IntegerField(default=0)
    payment_currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE, null=True, related_name='payment_currency_payment')
    exchange_rate = models.IntegerField(null=True)

class Subscription(models.Model):
    FREE = 0
    TRIAL = 1
    PREMIUM = 2
    SUBSCRIPTION_TYPE = (
        (FREE, 'FREE'),
        (TRIAL, 'TRIAL'),
        (PREMIUM, 'PREMIUM')
    )
    type = models.PositiveIntegerField(choices=SUBSCRIPTION_TYPE)
    code = models.CharField(max_length=32, default=generate_unique_code, editable=False)
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.PROTECT, related_name='tipster_subscriptions')
    subscriber = models.ForeignKey('core.UserAccount', on_delete=models.PROTECT, related_name='bettor_subscriptions')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, related_name='payment_subscription')
    period = models.IntegerField(default=-1)
    subscription_date = models.DateTimeField(auto_now=True)
    expiration_date = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.type}-{self.issuer.user.username}->{self.subscriber.user.username}'
