from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.backends.db import SessionStore
from rest_framework.request import Request
from mock import MagicMock


def get_mock_request(user):
    return MagicMock(
        spec=Request,
        user=user,
        session=SessionStore(session_key='bs64l1suajg97igcjfxgolfimd9fzkw9'),
        encoding='utf-8'
    )

mock_request = get_mock_request(AnonymousUser())