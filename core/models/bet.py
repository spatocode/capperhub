from django.db import models


class SportsEvent(models.Model):
    game = models.CharField(max_length=100)
    league = models.CharField(max_length=100)
    home = models.CharField(max_length=100)
    away = models.CharField(max_length=100)
    match_day = models.DateTimeField()
    result = models.CharField(max_length=10, null=True)

    def __str__(self):
        return f'{self.league}-{self.home[0:3]}:{self.away[0:3]}'


class P2PBet(models.Model):
    VOID = 0
    SETTLED = 1
    PENDING = 2
    STATUS = (
        (VOID, "VOID"),
        (SETTLED, "SETTLED"),
        (PENDING, "PENDING"),
    )
    backer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='issuer_bet')
    layer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='player_bet', null=True)
    event = models.ForeignKey('core.SportsEvent', on_delete=models.CASCADE)
    market = models.CharField(max_length=50)
    winner = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, null=True)
    placed_time = models.DateTimeField(auto_now_add=True)
    matched_time = models.DateTimeField()
    backer_option = models.BooleanField(null=True)
    layer_option = models.BooleanField(null=True)
    stake_per_bettor = models.FloatField()
    matched = models.BooleanField(default=False)
    currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE)
    is_public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING)


class P2PBetInvitation(models.Model):
    bet = models.ForeignKey('core.P2PBet', on_delete=models.CASCADE)
    requestor = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='requestor_request')
    requestee = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='requestee_request', null=True)
    date_initialized = models.DateTimeField(auto_now_add=True)
