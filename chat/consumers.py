import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        user = self.scope['user']
        if isinstance(user, AnonymousUser):
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'typing':
            await self.handle_typing_indicator(data)

    async def handle_chat_message(self, data):
        from .models import ChatRoom, Message
        from .serializers import MessageSerializer
        
        room = await ChatRoom.objects.aget(id=self.room_id)
        message = await Message.objects.acreate(
            room=room,
            sender=self.scope['user'],
            content=data['message']
        )
        
        serializer = MessageSerializer(message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': serializer.data
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))