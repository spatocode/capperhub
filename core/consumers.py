import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from core.shared.ws_utils import USER_GROUP_NAME_TPL, EventTypes


class UserUpdatesConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = USER_GROUP_NAME_TPL

        # Join user updates group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave user updates group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        """
        Dummy echo response for anything that is coming in 'echo_message' key of the payload
        plus current request user data in a separate key

        """
        print("RECEIVE", text_data)
        text_data_json = json.loads(text_data)
        message = text_data_json.get('echo_message')
        if message:
            # Send message to user updates group
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'user_update',
                    'event_type': EventTypes.TEST_ECHO,
                    'payload': {'message': message, 'group': self.group_name},
                }
            )

    def user_update(self, event):
        payload = event.get('payload', {})
        event_type = event.get('event_type')
        print("UPDATE", payload)
        self.send(text_data=json.dumps({
            'payload': payload,
            'event_type': event_type
        }))
