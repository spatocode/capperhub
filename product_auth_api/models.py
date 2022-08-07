from django.db import models
from django.contrib.auth.models import User

from product_api.models.base import Product


class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_account')
    is_predictor = models.BooleanField(default=False)
    country = models.CharField(max_length=50)
    mobile_no = models.IntegerField()
    subscribed_products = models.ManyToManyField(Product, related_name='subscribers')
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username}'
