import traceback as traceback
from urllib.parse import parse_qs
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from jwt import decode as jwt_decode
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
#from core.logger import logger

@database_sync_to_async
def get_user(id):
    User = get_user_model()
    try:
        return User.objects.get(id=id)
    except User.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware:
    """
    Custom token auth middleware
    """

    def __init__(self, inner):
        # Store the ASGI application we were passed
        self.inner = inner

    async def __call__(self, scope, receive, send):

        # Close old database connections to prevent usage of timed out connections
        close_old_connections()

        # Get the token
        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]

        # Try to authenticate the user
        try:
            # This will automatically validate the token and raise an error if token is invalid
            UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            # Token is invalid
            # logger.error({
            #     "message": e,
            #     "stacktrace": traceback.extract_stack()
            # })
            print(e)
            return None
        else:
            #  Then token is valid, decode it
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = await get_user(decoded_data["user_id"])

        # Return the inner application directly and let it run everything else
        return await self.inner(dict(scope, user=user), receive, send)

TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))
