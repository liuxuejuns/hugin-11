import time
import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
import redis
 
# pool = redis.ConnectionPool(
#     host="127.0.0.1",
#     port=6379,
#     max_connections=10,
#     decode_response=True,
# )
# conn = redis.Redis(connection_pool=pool, decode_responses=True)
userdict = dict()
 
class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.user = self.scope["url_route"]["kwargs"]["user"]
        # self.user_official = self.scope["user"]  # django 验证系统
        userdict[self.channel_name] = self.user
        self.room_group_name = "chat_%s" % self.room_name
 
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_connect",
                "message": "welcome %s join"%self.user
            }
        )
        await self.accept()
 
    async def disconnect(self, close_code):
        user = userdict[self.channel_name]
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_connect",
                "message": "%s disconnect"%user
            }
        )
        del userdict[self.channel_name]
 
    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": data["message"]
            }
        )
 
    async def chat_message(self, event):
        receive_message = event["message"]
        response_message = receive_message
        await self.send(text_data=response_message)

    async def chat_connect(self, event):
        receive_message = event["message"]
        await self.send(text_data=receive_message)
 
 