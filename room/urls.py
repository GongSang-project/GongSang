from django.urls import path
from . import views
from .views_list import room_list_page
from . import views_register as reg
from . import views_owner as own
from . import views_edit

app_name = 'room'

try:
    from .views_detail import room_detail, room_detail_test
    has_detail = True
except Exception:
    has_detail = False

urlpatterns = [
    path("senior/inbox/", views.senior_request_inbox, name="senior_request_inbox"),
    path("list/", room_list_page, name="room_list_page"),

    # 방 등록하기 - 등기부등본 업로드(시니어)
    path("register/deed/", reg.deed_start, name="deed_start"),
    path("register/deed/preview/", reg.deed_preview, name="deed_preview"),
    path("register/deed/retry/", reg.deed_retry, name="deed_retry"),
    path("register/deed/confirm/", reg.deed_confirm, name="deed_confirm"),

    # 방 등록하기 - 상세 정보 입력(시니어)
    path("register/step/address/", reg.register_step_address, name="register_step_address"),
    path("register/step/detail/",  reg.register_step_detail,  name="register_step_detail"),
    path("register/step/contract/", reg.register_step_contract, name="register_step_contract"),
    path("register/step/period/",  reg.register_step_period,  name="register_step_period"),
    path("register/step/facilities/", reg.register_step_facilities, name="register_step_facilities"),
    path("register/step/photos/", reg.register_step_photos, name="register_step_photos"),
    path("register/step/intro/",  reg.register_step_intro,  name="register_step_intro"),

    # 등록한 방 확인(시니어)
    path("my/", own.owner_room_list, name="owner_room_list"),
    path("my/<int:room_id>/edit/", views_edit.edit_start, name="owner_room_update"),
    path("my/<int:room_id>/delete/", own.owner_room_delete, name="owner_room_delete"),

    # 방 정보 수정하기(시니어)
    path("owner/rooms/<int:room_id>/edit/start/", views_edit.edit_start, name="owner_room_update_start"),
    path("owner/edit/address/",   views_edit.edit_step_address,   name="edit_step_address"),
    path("owner/edit/contract/",  views_edit.edit_step_contract,  name="edit_step_contract"),
    path("owner/edit/detail/",    views_edit.edit_step_detail,    name="edit_step_detail"),
    path("owner/edit/facilities/", views_edit.edit_step_facilities, name="edit_step_facilities"),
    path("owner/edit/photos/",    views_edit.edit_step_photos,    name="edit_step_photos"),

    # 리뷰 전체보기
    path("detail/<int:room_id>/reviews/", views.all_reviews_for_room, name="all_reviews_for_room"),
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
