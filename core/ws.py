from core.shared.ws_utils import EventTypes, notify_user_ws

def notify_update_user_subscribe(payload):
    notify_user_ws(EventTypes.SUBSCRIBE, payload)
    print("channels event ->", EventTypes.SUBSCRIBE)

def notify_update_user_unsubscribe(payload):
    notify_user_ws(EventTypes.UNSUBSCRIBE, payload)
    print("channels event ->", EventTypes.UNSUBSCRIBE)

def notify_update_user_play(payload):
    notify_user_ws(EventTypes.NEW_PLAY, payload)
    print("channels event ->", EventTypes.NEW_PLAY)

def notify_update_game_event(payload):
    notify_user_ws(EventTypes.NEW_SPORTS_EVENT, payload)
    print("channels event ->", EventTypes.NEW_SPORTS_EVENT)
