"""
ASGI config for hugin_L11 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application


# 下面记得如 将DjangoProject 修改为你们的项目名
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hugin_L11.settings')
django.setup()

django_asgi_app = get_asgi_application()

from django.urls import re_path, path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import testapp.routing

application = ProtocolTypeRouter(
    {
        # "http": django_asgi_app,
        'websocket': AuthMiddlewareStack(
            URLRouter(testapp.routing.websocket_urlpatterns)
        ),
    }
)
