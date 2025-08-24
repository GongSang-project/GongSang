from django.urls import path
from . import views

app_name = 'room'

urlpatterns = [
    path('detail/<int:room_id>/', views.room_detail, name='room_detail'),
    path('senior/inbox/', views.senior_request_inbox, name='senior_request_inbox'),

    path('detail/<int:room_id>/reviews/', views.all_reviews_for_room, name='all_reviews_for_room'),
]