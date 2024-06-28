from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import OriginValidator
import testapp.routing

application = ProtocolTypeRouter(
    {
        "websocket": OriginValidator(
            AuthMiddlewareStack(URLRouter(testapp.routing.websocket_urlpatterns)),
            # ["127.0.0.1","10.41.95.93","localhost:8080"]
            ["*"],
        )
    }
)
# application = ProtocolTypeRouter({
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             testapp.routing.websocket_urlpatterns
#         )
#     ),
# })
