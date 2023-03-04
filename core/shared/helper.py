import pytz
from datetime import datetime

from core.models.transaction import Transaction
from core.serializers import SportsWagerSerializer

def sync_records(self, sports_wager, layer, **kwargs):
    # Record Wagers
    sports_wager.layer = layer
    sports_wager.layer_option = kwargs.get("layer_option")
    sports_wager.matched = True
    sports_wager.matched_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
    sports_wager.save()

    # Record Wallets
    layer_wallet = layer.wallet
    layer_wallet.balance = layer_wallet.balance - sports_wager.stake
    layer_wallet.save()

    backer = sports_wager.backer
    backer_wallet = backer.wallet
    backer_wallet.withheld = backer_wallet.withheld - sports_wager.stake
    backer_wallet.save()

    # Record Transaction
    sports_wager.transaction.status = Transaction.SUCCEED
    sports_wager.transaction.save()
    Transaction.objects.create(
        type=Transaction.wager,
        amount=sports_wager.stake,
        balance=layer_wallet.balance,
        user=layer,
        status=Transaction.SUCCEED,
        currency=backer.currency
    )

    serializer = SportsWagerSerializer(sports_wager)
    return serializer