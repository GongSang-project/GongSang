from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'youth', 'senior', 'created_at')
    list_display_links = ('room', 'youth', 'senior',)
    list_filter = ('created_at',)
    search_fields = ('room__address', 'youth__username', 'senior__username',)
    raw_id_fields = ('room', 'youth', 'senior',)
    readonly_fields = ('created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chatroom', 'author', 'content', 'timestamp')
    list_display_links = ('content',)
    list_filter = ('timestamp',)
    search_fields = ('chatroom__room__address', 'author__username', 'content',)
    raw_id_fields = ('chatroom', 'author',)
    readonly_fields = ('timestamp',)