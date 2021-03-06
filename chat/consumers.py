import json
from os import name

from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Message, Room,User


class ChatConsumer(WebsocketConsumer):

    def fetch_messages(self,data):
        messages= Message.last_10_messages()
        content={
            'messages':self.messages_to_json(messages)
        }
        self.send_chat_message(content)

    def new_message(self,data):
        author=data['from']
        roomName=data['room']
        room=get_object_or_404(Room,name=roomName)
        author_user=User.objects.filter(username=author)[0]
        message=Message.objects.create(
            author=author_user,
            content=data['message'],
            room=room)
        content={
            'command':'new_message',
            'message':self.message_to_json(message)
        }
        return self.send_chat_message(content)


    def messages_to_json(self,messages):
        result=[]
        for message in messages:
            result.append(self.message_to_json(message))
        return result


    def message_to_json(self,message):
        if message.image:
            print(message.image)
        return {
            'author':message.author.username,
            'content':message.content,
            'timestamp':message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

    commands={
        'fetch_messages': fetch_messages,
        'new_message':new_message
    }

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        self.commands[data['command']](self,data)


    def send_chat_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
    

    def send_message(self,message):
        self.send(text_data=json.dumps(message))


    def chat_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps(message))
    
    def image_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({'type':'image_message','message':message}))