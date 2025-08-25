from django.urls import path
from . import views

# 리스트/등록/소유자 관련 뷰들
from .views_list import room_list_page
from . import views_register as reg
from . import views_owner as own
from . import views_edit

# 상세페이지가 분리되어 있는 경우 대비
try:
    from .views_detail import room_detail as detail_view, room_detail_test
    HAS_DETAIL = True
except Exception:
    detail_view = None
    room_detail_test = None
    HAS_DETAIL = False

app_name = 'room'

urlpatterns = [
    # 방 목록
    path("list/", room_list_page, name="room_list_page"),

    # 시니어 받은 요청함
    path("senior/inbox/", views.senior_request_inbox, name="senior_request_inbox"),

    # 방 등록하기 - 등기부등본 업로드(시니어)
    path("register/deed/",           reg.deed_start,   name="deed_start"),
    path("register/deed/preview/",   reg.deed_preview, name="deed_preview"),
    path("register/deed/retry/",     reg.deed_retry,   name="deed_retry"),
    path("register/deed/confirm/",   reg.deed_confirm, name="deed_confirm"),

    # 방 등록하기 - 상세 정보 입력(시니어)
    path("register/step/address/",    reg.register_step_address,     name="register_step_address"),
    path("register/step/detail/",     reg.register_step_detail,      name="register_step_detail"),
    path("register/step/contract/",   reg.register_step_contract,    name="register_step_contract"),
    path("register/step/period/",     reg.register_step_period,      name="register_step_period"),
    path("register/step/facilities/", reg.register_step_facilities,  name="register_step_facilities"),
    path("register/step/photos/",     reg.register_step_photos,      name="register_step_photos"),
    path("register/step/intro/",      reg.register_step_intro,       name="register_step_intro"),

    # 방 등록하기 - 등기부등본 업로드(시니어)
    path("register/deed/",           reg.deed_start,   name="deed_start"),
    path("register/deed/preview/",   reg.deed_preview, name="deed_preview"),
    path("register/deed/preview/stream/", reg.deed_preview_stream, name="deed_preview_stream"), # 이 줄을 추가
    path("register/deed/retry/",     reg.deed_retry,   name="deed_retry"),
    path("register/deed/confirm/",   reg.deed_confirm, name="deed_confirm"),

    # 등록한 방(시니어)
    path("my/",                    own.owner_room_list,     name="owner_room_list"),
    path("my/<int:room_id>/edit/", views_edit.edit_start,   name="owner_room_update"),
    path("my/<int:room_id>/delete/", own.owner_room_delete, name="owner_room_delete"),

    # 방 정보 수정하기(시니어)
    path("owner/rooms/<int:room_id>/edit/start/", views_edit.edit_start,            name="owner_room_update_start"),
    path("owner/edit/address/",                   views_edit.edit_step_address,     name="edit_step_address"),
    path("owner/edit/contract/",                  views_edit.edit_step_contract,    name="edit_step_contract"),
    path("owner/edit/detail/",                    views_edit.edit_step_detail,      name="edit_step_detail"),
    path("owner/edit/facilities/",                views_edit.edit_step_facilities,  name="edit_step_facilities"),
    path("owner/edit/photos/",                    views_edit.edit_step_photos,      name="edit_step_photos"),

    # 리뷰 전체보기
    path("detail/<int:room_id>/reviews/", views.all_reviews_for_room, name="all_reviews_for_room"),
]

# 상세 페이지 라우트 (views_detail이 있으면 우선)
if HAS_DETAIL and detail_view:
    urlpatterns += [
        path("detail/<int:room_id>/", detail_view, name="room_detail"),
    ]
    if room_detail_test:
        urlpatterns += [
            path("detail-test/<int:room_id>/", room_detail_test, name="room_detail_test"),
        ]
else:
    urlpatterns += [
        path("detail/<int:room_id>/", views.room_detail, name="room_detail"),
    ]
