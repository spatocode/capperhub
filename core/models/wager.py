from django.db import models
from core.shared.model_utils import generate_wager_id

class SportsWager(models.Model):
    VOID = 0
    SETTLED = 1
    PENDING = 2
    STATUS = (
        (VOID, "VOID"),
        (SETTLED, "SETTLED"),
        (PENDING, "PENDING"),
    )
    id = models.CharField(max_length=10, default=generate_wager_id, primary_key=True, editable=False)
    backer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='backer_wager')
    layer = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='layer_wager', null=True)
    game = models.ForeignKey('core.SportsGame', on_delete=models.CASCADE, related_name="wagers")
    market = models.CharField(max_length=50)
    winner = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, null=True)
    placed_time = models.DateTimeField(auto_now_add=True)
    matched_time = models.DateTimeField(null=True)
    backer_option = models.BooleanField()
    layer_option = models.BooleanField(null=True)
    stake = models.FloatField()
    matched = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING)
    transaction = models.ForeignKey('core.Transaction', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.id}-{self.backer}'


class SportsWagerChallenge(models.Model):
    wager = models.ForeignKey('core.SportsWager', on_delete=models.CASCADE, related_name="invitation")
    requestor = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='requestor_request')
    requestee = models.ForeignKey('core.UserAccount', on_delete=models.CASCADE, related_name='requestee_request', null=True)
    date_initialized = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.requestor.user.username}-{self.wager.id}'
