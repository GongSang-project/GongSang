from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('senior/', views.review_list_senior, name='review_list_senior'),
    path('senior/completed/', views.review_completed_list_senior, name='review_completed_list_senior'),

    path('write/<int:request_id>/', views.review_write, name='review_write'),

    path('youth/', views.review_list_youth, name='review_list_youth'),
    path('youth/completed/', views.review_completed_list_youth, name='review_completed_list_youth'),
]