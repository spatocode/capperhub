from django.db import models

from product_api.models.base import Product


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
    name = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.name}'


class FootballPrediction(models.Model):
    type = models.PositiveIntegerField(choices=PREDICTION_TYPES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='football_predictions')
    home_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name='home_team')
    away_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name='away_team')
    match_day = models.DateTimeField()
    pick = models.CharField(max_length=15)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.home_team} - {self.away_team}'
