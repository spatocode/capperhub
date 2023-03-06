import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from core.middleware import TokenAuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "predishun.settings")
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

import core.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            TokenAuthMiddlewareStack(URLRouter(core.routing.websocket_urlpatterns))
        ),
    }
)
