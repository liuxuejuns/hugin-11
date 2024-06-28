
# mysite/chat/routing.py
 
from django.urls import re_path, path
from testapp import consumers
 
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/(?P<user>\w+)/$", consumers.ChatConsumer.as_asgi()),
]