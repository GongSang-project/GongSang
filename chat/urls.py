from django.urls import path
from . import views

urlpatterns = [
    path('create-or-get-chatroom/', views.create_or_get_chatroom, name='create_or_get_chatroom'),
    path('send-message/', views.send_message, name='send_message'),
    path('get-messages/<int:chatroom_id>/', views.get_messages, name='get_messages'),
    path('chatroom/<int:chatroom_id>/', views.chatroom_detail, name='chatroom_detail'),
    path('send-message/', views.send_message, name='send_message'),
    path('get-messages/<int:chatroom_id>/', views.get_messages, name='get_messages'),
]