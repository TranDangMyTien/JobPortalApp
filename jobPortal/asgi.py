import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import jobs.routing
from dotenv import load_dotenv
load_dotenv()


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobPortal.settings')
# os.environ.get('DJANGO_SETTINGS_MODULE')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                jobs.routing.websocket_urlpatterns
            )
        )
    ),
})

