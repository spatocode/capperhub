from django.db import models
from core.models.transaction import Transaction
from core.shared.model_utils import generate_unique_code

class Subscription(models.Model):
    FREE = 0
    PREMIUM = 1
    SUBSCRIPTION_TYPE = (
        (FREE, 'FREE'),
        (PREMIUM, 'PREMIUM')
    )
    type = models.PositiveIntegerField(choices=SUBSCRIPTION_TYPE)
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.PROTECT, related_name='issuer_subscriptions')
    subscriber = models.ForeignKey('core.UserAccount', on_delete=models.PROTECT, related_name='subscriber_subscriptions')
    period = models.IntegerField(default=-1)
    subscription_date = models.DateTimeField(auto_now=True)
    expiration_date = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.type}-{self.issuer.user.username}->{self.subscriber.user.username}'
