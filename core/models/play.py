from django.db import models

class Play(models.Model):
    LOSS = 0
    WIN = 1
    PENDING = 2
    STATUS = (
        (LOSS, "LOSS"),
        (WIN, "WIN"),
        (PENDING, "PENDING")
    )
    sports = models.CharField(max_length=20)
    issuer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE)
    competition = models.CharField(max_length=50)
    home_team = models.CharField(max_length=50)
    away_team = models.CharField(max_length=50)
    prediction = models.CharField(max_length=50)
    match_day = models.DateTimeField()
    date_added = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=10, null=True)
    is_premium = models.BooleanField(default=True)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING)

    def __str__(self):
        return f'{self.sports}-{self.issuer.user.username}'
