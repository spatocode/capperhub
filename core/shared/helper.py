import pytz
from datetime import datetime

from core.models.transaction import Transaction
from core.serializers import P2PSportsBetSerializer

def sync_records(self, p2psportsbet, layer, **kwargs):
    # Record Wagers
    p2psportsbet.layer = layer
    p2psportsbet.layer_option = kwargs.get("layer_option")
    p2psportsbet.matched = True
    p2psportsbet.matched_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
    p2psportsbet.save()

    # Record Wallets
    layer_wallet = layer.wallet
    layer_wallet.balance = layer_wallet.balance - p2psportsbet.stake
    layer_wallet.save()

    backer = p2psportsbet.backer
    backer_wallet = backer.wallet
    backer_wallet.withheld = backer_wallet.withheld - p2psportsbet.stake
    backer_wallet.save()

    # Record Transaction
    p2psportsbet.transaction.status = Transaction.SUCCEED
    p2psportsbet.transaction.save()
    Transaction.objects.create(
        type=Transaction.BET,
        amount=p2psportsbet.stake,
        balance=layer_wallet.balance,
        user=layer,
        status=Transaction.SUCCEED,
        currency=backer.currency
    )

    serializer = P2PSportsBetSerializer(p2psportsbet)
    return serializer