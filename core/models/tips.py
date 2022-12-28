from django.db import models

class Game(models.Model):
    type = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.type}'

class Tips(models.Model):
    LOSS = 0
    WIN = 1
    PENDING = 2
    STATUS = (
        (LOSS, "LOSS"),
        (WIN, "WIN"),
        (PENDING, "PENDING")
    )
    game = models.ForeignKey('core.Game', on_delete=models.PROTECT, related_name='tips')
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE)
    league = models.CharField(max_length=20)
    home_team = models.CharField(max_length=50)
    away_team = models.CharField(max_length=50)
    prediction = models.CharField(max_length=50)
    date = models.DateTimeField()
    result = models.CharField(max_length=10, null=True)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING)

    def __str__(self):
        return f'{self.game.type}-{self.issuer.user.username}'
