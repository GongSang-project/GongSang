from django.urls import path
from . import views

urlpatterns = [
    path('detail/<int:room_id>/', views.room_detail, name='room_detail'),
]