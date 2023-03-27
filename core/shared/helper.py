import pytz
from datetime import datetime
from django.conf import settings
import telebot
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser, InputPeerChannel
from telethon import TelegramClient, sync, events

from core.models.transaction import Transaction
from core.models.subscription import Subscription
from core.serializers import SportsWagerSerializer
from core import ws

def sync_subscriptions(**kwargs):
    if kwargs.get("issuer"):
        premium_subscriptions = Subscription.objects.filter(
            issuer=kwargs.get("issuer"),
            type=1,
            is_active=True,
            expiration_date__lt=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
    else:
        premium_subscriptions = Subscription.objects.filter(
            subscriber=kwargs.get("subscriber"),
            type=1,
            is_active=True,
            expiration_date__lt=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
    for premium in premium_subscriptions:
        premium.is_active = False
        premium.save()

def sync_records(sports_wager, layer, **kwargs):
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
        type=Transaction.WAGER,
        amount=sports_wager.stake,
        balance=layer_wallet.balance,
        user=layer,
        status=Transaction.SUCCEED,
        currency=backer.currency
    )

    serializer = SportsWagerSerializer(sports_wager)
    return serializer


def notify_telegram_users():
    client = TelegramClient('session', settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    client.connect()

    if not client.is_user_authorized():  
        client.send_code_request(settings.TELEGRAM_PHONE_NUMBER)
        
        # signing in the client
        client.sign_in(settings.TELEGRAM_PHONE_NUMBER, input('Enter the code: '))

def notify_whatsapp_users():
    pass

def notify_subscribers(data):
    ws.notify_update_user_play(data)
