from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    path('request/<int:room_id>/', views.request_move_in, name='request_move_in'),
]