from core.models.user import UserAccount
from core.shared.ws_utils import EventTypes, notify_user_ws

def notify_update_user_subscribe(issuer, payload):
    notify_user_ws(issuer, EventTypes.USER_SUBSCRIBED, payload)
    print("Notified", EventTypes.USER_SUBSCRIBED)

def notify_update_user_unsubscribe(issuer, payload):
    notify_user_ws(issuer, EventTypes.USER_UNSUBSCRIBED, payload)
    print("Notified", EventTypes.USER_UNSUBSCRIBED)

def notify_update_user_play(request, payload):
    subscriptions = request.user.useraccount.issuer_subscriptions.filter(
        type= 1 if request.data.get("is_premium") else 0,
        is_active=True,
    )
    for subscription in subscriptions:
        notify_user_ws(subscription.subscriber.id, EventTypes.USER_BROADCAST_PLAY, payload)
    print("Notified", EventTypes.USER_BROADCAST_PLAY)

def notify_update_game_event(payload):
    userAccounts = UserAccount.objects.filter(user__is_active=True)
    for userAccount in userAccounts:
        notify_user_ws(userAccount.user.id, EventTypes.USER_CREATE_GAME_EVENT, payload)
    print("Notified", EventTypes.USER_CREATE_GAME_EVENT)
