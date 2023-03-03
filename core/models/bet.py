from django.db import models
from core.shared.model_utils import generate_bet_id

class SportsEvent(models.Model):
    type = models.CharField(max_length=100)
    competition = models.CharField(max_length=100)
    home = models.CharField(max_length=100)
    away = models.CharField(max_length=100)
    match_day = models.DateTimeField()
    result = models.CharField(max_length=10, null=True)
    added_by = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, null=True)
    time_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.competition}-{self.home[0:3]}:{self.away[0:3]}'


class P2PSportsBet(models.Model):
    VOID = 0
    SETTLED = 1
    PENDING = 2
    STATUS = (
        (VOID, "VOID"),
        (SETTLED, "SETTLED"),
        (PENDING, "PENDING"),
    )
    id = models.CharField(max_length=6, default=generate_bet_id, primary_key=True, editable=False)
    backer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='backer_bet')
    layer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='layer_bet', null=True)
    event = models.ForeignKey('core.SportsEvent', on_delete=models.CASCADE)
    market = models.CharField(max_length=50)
    winner = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, null=True)
    placed_time = models.DateTimeField(auto_now_add=True)
    matched_time = models.DateTimeField(null=True)
    backer_option = models.BooleanField()
    layer_option = models.BooleanField(null=True)
    stake = models.FloatField()
    matched = models.BooleanField(default=False)
    currency = models.ForeignKey('core.Currency', on_delete=models.CASCADE, null=True)
    is_public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING)
    transaction = models.ForeignKey('core.Transaction', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.id}-{self.backer}'


class P2PSportsBetInvitation(models.Model):
    bet = models.ForeignKey('core.P2PSportsBet', on_delete=models.CASCADE, related_name="invitation")
    requestor = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='requestor_request')
    requestee = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='requestee_request', null=True)
    date_initialized = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.requestor.user.username}-{self.bet.id}'
