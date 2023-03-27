from django.db import models

class PlaySlip(models.Model):
    title = models.CharField(max_length=100, default="")
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    is_premium = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.title}'


class Play(models.Model):
    LOSS = 0
    WIN = 1
    PENDING = 2
    STATUS = (
        (LOSS, "LOSS"),
        (WIN, "WIN"),
        (PENDING, "PENDING")
    )
    slip = models.ForeignKey('core.PlaySlip', on_delete=models.CASCADE)
    sports = models.CharField(max_length=20)
    competition = models.CharField(max_length=50)
    home_team = models.CharField(max_length=50)
    away_team = models.CharField(max_length=50)
    prediction = models.CharField(max_length=50)
    match_day = models.DateTimeField()
    result = models.CharField(max_length=10, null=True)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING)
    # analysis = models.TextField(default="")

    def __str__(self):
        return f'{self.sports}-{self.slip.issuer.user.username}'
