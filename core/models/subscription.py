from django.db import models
from django.utils.timezone import now
from core.shared.model_utils import generate_unique_code

SUBSCRIPTION_TYPE = (
    (0, 'FREE'),
    (1, 'TRIAL'),
    (2, 'PREMIUM')
)

class Subscription(models.Model):
    type = models.PositiveIntegerField(choices=SUBSCRIPTION_TYPE)
    code = models.CharField(max_length=32, default=generate_unique_code)
    price = models.IntegerField(default=0)
    currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE, null=True)
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='subscription')
    subscriber = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='subscription')
    period = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now=True)
