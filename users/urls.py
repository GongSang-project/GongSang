from django.urls import path
from .views import SurveyWizard, FORMS
from . import views

app_name = 'users'

urlpatterns = [
    path('survey/', SurveyWizard.as_view(FORMS), name='survey_wizard'),
    path('select_user/', views.user_selection, name='user_selection'),
    path('home/youth/', views.home_youth, name='home_youth'),
    path('home/senior/', views.home_senior, name='home_senior'),
    path('login/<str:user_type>/', views.login_as_user, name='login_as_user'),
    path('logout/', views.user_logout, name='user_logout'),
    path('upload_id_card/', views.upload_id_card, name='upload_id_card'),
    path('upload_land_register/', views.upload_land_register, name='upload_land_register'),
]