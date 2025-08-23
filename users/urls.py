from django.urls import path
from .views import SurveyWizard, FORMS
from . import views

app_name = 'users'

urlpatterns = [
    # 설문조사 시작점 (단계 이름 없음)
    path('survey/', SurveyWizard.as_view(FORMS), name='survey_wizard_start'),
    # 설문조사 단계별 URL (단계 이름 포함)
    path('survey/<str:step>/', SurveyWizard.as_view(FORMS), name='survey_wizard_step'),

    path('select_user/', views.user_selection, name='user_selection'),
    path('login/<str:user_type>/', views.login_as_user, name='login_as_user'),
    path('user_info/', views.user_info_view, name='user_info'),
    path('youth-region/', views.youth_region_view, name='youth_region'),
    path('senior-living-type/', views.senior_living_type_view, name='senior_living_type'),
    path('upload-id-card/', views.upload_id_card, name='upload_id_card'),
    path('home/youth/', views.home_youth, name='home_youth'),
    path('home/senior/', views.home_senior, name='home_senior'),
    path('logout/', views.user_logout, name='user_logout'),

    path('senior/<int:senior_id>/room/<int:room_id>/', views.senior_profile, name='senior_profile'),
    path('profile/youth/<int:request_id>/', views.youth_profile, name='youth_profile'),
    path('profile/youth/<int:youth_id>/reviews/', views.all_reviews_for_youth, name='all_reviews'),

    path('senior/mypage/', views.senior_info_view, name='senior_info'),
    path('youth/mypage/', views.youth_info_view, name='youth_info'),
]