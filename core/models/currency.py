from django.core.validators import RegexValidator
from django.db import models
from django_countries.fields import CountryField

class Currency(models.Model):
    code_validator = RegexValidator(
        regex='[A-Z]{3}',
        message='Please enter a valid 3-letter currency code'
    )
    code = models.CharField(max_length=3, primary_key=True, validators=[code_validator])
    country = CountryField()

    def __str__(self):
        return f'{self.code}'