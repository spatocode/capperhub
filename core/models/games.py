from django.db import models
from django.contrib.postgres.fields import ArrayField


def default_markets():
    return ["Home win", "Draw", "Away win", "Home 1st Goal", "Away 1st Goal"
    ]

class Market(models.Model):
    name = models.CharField(max_length=50)
    sport = models.ForeignKey("core.Sport", on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name}'


class Sport(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.name}'

class Competition(models.Model):
    name = models.CharField(max_length=50)
    sport = models.ForeignKey("core.Sport", on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name}'

class Team(models.Model):
    name = models.CharField(max_length=50)
    competition = models.ManyToManyField(Competition)

    def __str__(self):
        return f'{self.name}'

class SportsGame(models.Model):
    type = models.ForeignKey("core.Sport", on_delete=models.PROTECT, related_name="sports_game")
    competition = models.CharField(max_length=100)
    home = models.CharField(max_length=100)
    away = models.CharField(max_length=100)
    match_day = models.DateTimeField()
    result = models.CharField(max_length=10, default="", blank=True)
    time_added = models.DateTimeField(auto_now_add=True)
    markets = ArrayField(models.CharField(max_length=50), default=default_markets)
    is_wager_played = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.competition}-{self.home[0:3]}:{self.away[0:3]}'
