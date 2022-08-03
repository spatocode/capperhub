from django.db import models

from product_app.models.base import Product


WIN = 0
DRAW = 1
DOUBLE_CHANCE = 2
ONE_POINT_FIVE = 3
TWO_POINT_FIVE = 4
CORRECT_SCORE = 5

PREDICTION_TYPES = (
    (WIN, 'WIN'),
    (DRAW, 'DRAW'),
    (DOUBLE_CHANCE, 'DOUBLE_CHANCE'),
    (ONE_POINT_FIVE, '1.5'),
    (TWO_POINT_FIVE, '2.5'),
    (CORRECT_SCORE, 'CORRECT_SCORE'),
)

class FootballTeam(models.Model):
    name = models.CharField()


class FootballPrediction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.PositiveIntegerField(choices=PREDICTION_TYPES)
    home_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE)
    away_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE)
    match_day = models.DateTimeField()
    pick = models.CharField()
