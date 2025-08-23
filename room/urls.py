from django.urls import path
from . import views
from .views_list import room_list_page
from . import views_register as reg
from . import views_owner as own

app_name = 'room'

try:
    from .views_detail import room_detail, room_detail_test
    has_detail = True
except Exception:
    has_detail = False

urlpatterns = [
    path("senior/inbox/", views.senior_request_inbox, name="senior_request_inbox"),
    path("list/", room_list_page, name="room_list_page"),

    #path("api/addr/sido/", reg.addr_sido_list, name="addr_sido_list"),
    #path("api/addr/sigungu/", reg.addr_sigungu_list, name="addr_sigungu_list"),
    #path("api/addr/dong/", reg.addr_dong_list, name="addr_dong_list"),

    # 등기부
    path("register/deed/", reg.deed_start, name="deed_start"),
    #path("register/deed/camera/", reg.deed_upload_camera, name="deed_upload_camera"),
    #path("register/deed/file/", reg.deed_upload_file, name="deed_upload_file"),
    path("register/deed/preview/", reg.deed_preview, name="deed_preview"),
    path("register/deed/retry/", reg.deed_retry, name="deed_retry"),
    path("register/deed/confirm/", reg.deed_confirm, name="deed_confirm"),

    # 스텝
    path("register/step/address/", reg.register_step_address, name="register_step_address"),
    path("register/step/detail/",  reg.register_step_detail,  name="register_step_detail"),
    path("register/step/contract/",reg.register_step_contract,name="register_step_contract"),
    path("register/step/period/",  reg.register_step_period,  name="register_step_period"),
    path("register/step/facilities/", reg.register_step_facilities, name="register_step_facilities"),
    path("register/step/photos/", reg.register_step_photos, name="register_step_photos"),
    path("register/step/intro/",  reg.register_step_intro,  name="register_step_intro"),

    # 시니어 - 내 방 관리
    path("my/", own.owner_room_list, name="owner_room_list"),
    path("my/<int:room_id>/edit/", own.owner_room_update, name="owner_room_update"),
    path("my/<int:room_id>/delete/", own.owner_room_delete, name="owner_room_delete"),
]

if has_detail:
    urlpatterns += [
        path("detail/<int:room_id>/", room_detail, name="room_detail"),
        path("detail-test/<int:room_id>/", room_detail_test, name="room_detail_test"),
    ]
else:
    urlpatterns += [
        path("detail/<int:room_id>/", views.room_detail, name="room_detail"),
    ]