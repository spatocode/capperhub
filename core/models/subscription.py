from datetime import datetime, timedelta

from django.db import models
import pytz

class Subscription(models.Model):
    user = models.ForeignKey('core.UserAccount', on_delete=models.PROTECT, related_name='premium_subscription', editable=False)
    period = models.IntegerField(editable=False) # in days
    amount = models.IntegerField(editable=False)
    time = models.DateTimeField(auto_now=True, editable=False)
    expiration = models.DateTimeField(editable=False)

    @property
    def is_active(self):
        return datetime.utcnow().replace(tzinfo=pytz.UTC) < self.expiration

    def __str__(self):
        return f'{self.user.user.username}'
