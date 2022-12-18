from django.db import models

class Game(models.Model):
    type = models.CharField(max_length=30)

    def __str__(self):
        return f'{self.type}'

class Tips(models.Model):
    game = models.ForeignKey('core.Game', on_delete=models.PROTECT, related_name='tips')
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE)
    home_team = models.CharField(max_length=50)
    away_team = models.CharField(max_length=50)
    prediction = models.CharField(max_length=50)
    date = models.DateTimeField()
    success = models.BooleanField(default=False)
    published = models.BooleanField(default=False)

    class Meta:
        unique_together = ('game', 'issuer', 'home_team', 'away_team', 'date')

    def __str__(self):
        return f'{self.game.type}-{self.issuer.user.username}'
