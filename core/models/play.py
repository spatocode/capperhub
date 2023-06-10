from django.db import models

class PlaySlip(models.Model):
    title = models.CharField(max_length=100, default="")
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    is_premium = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.title}'


class Match(models.Model):
    sports = models.CharField(max_length=20)
    competition = models.CharField(max_length=50)
    home_team = models.CharField(max_length=50)
    away_team = models.CharField(max_length=50)
    match_day = models.DateTimeField()
    result = models.CharField(max_length=10, null=True)


class Play(models.Model):
    LOSS = 0
    WIN = 1
    PENDING = 2
    STATUS = (
        (LOSS, "LOSS"),
        (WIN, "WIN"),
        (PENDING, "PENDING")
    )
    match = models.ForeignKey('core.Match', on_delete=models.CASCADE, null=True)
    slip = models.ForeignKey('core.PlaySlip', on_delete=models.CASCADE)    
    prediction = models.CharField(max_length=50)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING)

    def __str__(self):
        return f'{self.match.sports}-{self.slip.issuer.user.username}'
