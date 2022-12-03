from django.db import models


FOOTBALL = 0
BASKETBALL = 1
BASEBALL = 2
SPORTS = (
    (FOOTBALL, 'FOOTBALL'),
    (BASKETBALL, 'BASKETBALL'),
    (BASEBALL, 'BASEBALL'),
)

class SportsTips(models.Model):
    owner = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE)
    sport = models.PositiveIntegerField(choices=SPORTS)
    home_team = models.CharField(max_length=50)
    away_team = models.CharField(max_length=50)
    prediction = models.CharField(max_length=50)
    match_day = models.DateTimeField()
    success = models.BooleanField(default=False)

    class Meta:
        unique_together = ('sport', 'owner')
    
    def __str__(self):
        return f'{SPORTS[self.sport][1]}-{self.owner.user.username}'