import channels.layers
from asgiref.sync import async_to_sync

USER_GROUP_NAME_TPL = 'user_updates'


class EventTypes:
    TEST_ECHO = 'TEST_ECHO'
    USER_SUBSCRIBED = 'USER_SUBSCRIBED'
    USER_UNSUBSCRIBED = 'USER_UNSUBSCRIBED'
    USER_BROADCAST_PLAY = 'USER_BROADCAST_PLAY'
    USER_CREATE_GAME_EVENT = 'USER_CREATE_GAME_EVENT'


def notify_user_ws(user_pk, event_type, payload):
    assert type(user_pk) is int
    # todo validate event_type?
    assert isinstance(payload, dict), "event_data is not a dict"

    # Send a message to user updates group
    channels_group_name = USER_GROUP_NAME_TPL
    channel_layer = channels.layers.get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        channels_group_name,
        {
            # django-channels special key for binding a corresponding consumer method
            'type': 'user_update',
            # internal type to sync the front end actions (see EventTypes const class)
            'event_type': event_type,
            'payload': payload
        }
    )
