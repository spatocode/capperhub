from django.core.validators import RegexValidator
from django.db import models

FOOTBALL = 0
BASKETBALL = 1
BASEBALL = 2
PRODUCT_TYPES = (
    (FOOTBALL, 'FOOTBALL'),
    (BASKETBALL, 'BASKETBALL'),
    (BASEBALL, 'BASEBALL'),
)

class Currency(models.Model):
    code_validator = RegexValidator(
        regex='[A-Z]{3}',
        message='Please enter a valid 3-letter currency code'
    )
    code = models.CharField(max_length=3, primary_key=True, validators=[code_validator])

    def __str__(self):
        return f'{self.code}'


class Product(models.Model):
    type = models.PositiveIntegerField(choices=PRODUCT_TYPES)
    owner = models.ForeignKey('product_auth_api.UserAccount', on_delete=models.CASCADE, related_name='products')
    price = models.IntegerField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('type', 'owner')
    
    def __str__(self):
        return f'{PRODUCT_TYPES[self.type][1]}-{self.owner.user.username}'
