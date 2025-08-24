from django.urls import path
from . import views
from .views_list import room_list_page

app_name = 'room'

try:
    from .views_detail import room_detail, room_detail_test
    has_detail = True
except Exception:
    has_detail = False

urlpatterns = [
    path("senior/inbox/", views.senior_request_inbox, name="senior_request_inbox"),
    path("list/", room_list_page, name="room_list_page"),
]
    path('detail/<int:room_id>/', views.room_detail, name='room_detail'),
    path('senior/inbox/', views.senior_request_inbox, name='senior_request_inbox'),

if has_detail:
    urlpatterns += [
        path("detail/<int:room_id>/", room_detail, name="room_detail"),
        path("detail-test/<int:room_id>/", room_detail_test, name="room_detail_test"),
    ]
else:
    urlpatterns += [
        path("detail/<int:room_id>/", views.room_detail, name="room_detail"),
    ]