from django.db import models
from django.conf import settings
from room.models import Room

class ChatRoom(models.Model):
    # 채팅방의 대상이 되는 방 객체
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='chat_rooms')

    # 채팅방을 개설한 청년 유저
    youth = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='youth_chat_rooms')

    # 채팅방의 주인인 노인 유저 (room.owner와 동일)
    senior = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='senior_chat_rooms')

    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)