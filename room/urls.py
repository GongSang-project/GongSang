from django.urls import path
from . import views

urlpatterns = [
    path('detail-test/<int:room_id>/', views.room_detail_test, name='room_detail_test'),
]