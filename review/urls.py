from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('', views.review_list, name='review_list'),
    path('completed/', views.review_completed_list, name='review_completed_list'),
    path('write/<int:request_id>/', views.review_write, name='review_write'),
]