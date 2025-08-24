from django.urls import path
from .views import SurveyWizard, FORMS
from . import views
# from . import views_public

app_name = 'users'

urlpatterns = [
    # 설문조사
    path('survey/', SurveyWizard.as_view(FORMS), name='survey_wizard_start'),
    path('survey/<str:step>/', SurveyWizard.as_view(FORMS), name='survey_wizard_step'),

    # 공통/인증
    path('select_user/', views.user_selection, name='user_selection'),
    path('login/<str:user_type>/', views.login_as_user, name='login_as_user'),
    path('logout/', views.user_logout, name='user_logout'),

    # 기본 정보/뷰
    path('user_info/', views.user_info_view, name='user_info'),
    path('home/youth/', views.home_youth, name='home_youth'),
    path('home/senior/', views.home_senior, name='home_senior'),

    # 설문 세부 단계
    path('youth-region/', views.youth_region_view, name='youth_region'),
    path('senior-living-type/', views.senior_living_type_view, name='senior_living_type'),
    path('upload-id-card/', views.upload_id_card, name='upload_id_card'),

    # 프로필/리뷰
    path('senior/<int:senior_id>/room/<int:room_id>/', views.senior_profile, name='senior_profile'),
    path('profile/youth/<int:request_id>/', views.youth_profile, name='youth_profile'),
    path('profile/youth/<int:youth_id>/reviews/', views.all_reviews_for_youth, name='all_reviews'),

    # 마이페이지
    path('senior/mypage/', views.senior_info_view, name='senior_info'),
    path('youth/mypage/', views.youth_info_view, name='youth_info'),
    path('youth/mypage/my_reviews/', views.my_reviews, name='my_reviews'),

    path('home/youth/all_rooms/', views.all_rooms_youth, name='all_rooms_youth'),
    path('api/region-autocomplete/', views.autocomplete_region, name='region_autocomplete'),
    path('list/', views.listings_by_region, name='room_list_page'),  # (주의) users 네임스페이스 내 name
]
