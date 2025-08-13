from django.contrib.auth.decorators import login_required
from formtools.wizard.views import SessionWizardView
from django.shortcuts import redirect, render
from .forms import (
    SurveyStep1Form,
    SurveyStep2Form,
    SurveyStep3Form,
    SurveyStep4Form,
    SurveyStep5Form,
    SurveyStep6Form,
    SurveyStep7Form,
    SurveyStep8Form,
    SurveyStep9Form,
    SurveyStep10Form,
)
from .models import User

from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout

from .forms import IdCardForm, LandRegisterForm


FORMS = [
    ("step1", SurveyStep1Form),
    ("step2", SurveyStep2Form),
    ("step3", SurveyStep3Form),
    ("step4", SurveyStep4Form),
    ("step5", SurveyStep5Form),
    ("step6", SurveyStep6Form),
    ("step7", SurveyStep7Form),
    ("step8", SurveyStep8Form),
    ("step9", SurveyStep9Form),
    ("step10", SurveyStep10Form),
]


class SurveyWizard(SessionWizardView):
    def get_template_names(self):
        return ['users/survey_form.html']

    def post(self, request, *args, **kwargs):
        # '건너뛰기' 버튼이 눌렸는지 확인
        if 'skip_step' in request.POST:
            # 현재 폼의 데이터는 세션에 저장
            current_form = self.get_form(data=self.request.POST, files=self.request.FILES)
            if current_form.is_valid():
                self.storage.set_step_data(self.steps.current, self.get_form_step_data(current_form))
            # `done` 메서드를 호출하여 설문 완료 처리
            return self.done(self.get_form_list(), **kwargs)

        return super().post(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        form_data = self.get_all_cleaned_data()
        user = self.request.user

        # 모든 폼의 데이터를 모델 필드에 저장.
        # 데이터가 없는 필드는 기본값 유지.
        user.preferred_time = form_data.get('preferred_time', user.preferred_time)
        user.conversation_style = form_data.get('conversation_style', user.conversation_style)
        user.important_points = form_data.get('important_points', user.important_points)
        user.meal_preference = form_data.get('meal_preference', user.meal_preference)
        user.weekend_preference = form_data.get('weekend_preference', user.weekend_preference)
        user.smoking_preference = form_data.get('smoking_preference', user.smoking_preference)
        user.noise_level = form_data.get('noise_level', user.noise_level)
        user.space_sharing_preference = form_data.get('space_sharing_preference', user.space_sharing_preference)
        user.pet_preference = form_data.get('pet_preference', user.pet_preference)
        user.wishes = form_data.get('wishes', user.wishes)

        user.save()
        self.storage.reset()  # 세션 데이터 초기화

        if user.is_youth:
            return redirect('users:home_youth')
        else:
            return redirect('users:home_senior')

def user_selection(request):
    if request.user.is_authenticated:
        if request.user.is_youth:
            return redirect('users:home_youth')
        else:
            return redirect('users:home_senior')
    return render(request, 'users/user_selection.html')

def login_as_user(request, user_type):
    user = None

    if user_type == 'youth':
        user, created = User.objects.get_or_create(
            username='김청년',
            defaults={
                'is_youth': True,
            }
        )

    elif user_type == 'senior':
        user, created = User.objects.get_or_create(
            username='박노인',
            defaults={
                'is_youth': False,
            }
        )

    if user:
        auth_login(request, user)
        print(f"로그인 성공: {user.username} (청년: {user.is_youth})")

        if not user.is_id_card_uploaded:
            return redirect('users:upload_id_card')
        if not user.is_youth and not user.is_land_register_uploaded:
            return redirect('users:upload_land_register')

        if user.is_youth:
            return redirect('users:home_youth')
        else:
            return redirect('users:home_senior')

        #return redirect('users:survey_wizard')

    else:
        return render(request, 'users/user_selection.html', {'error_message': '사용자를 찾거나 생성할 수 없습니다.'})

def home_youth(request):
    return render(request, 'users/home_youth.html')

def home_senior(request):
    return render(request, 'users/home_senior.html')

def user_logout(request):
    auth_logout(request)
    return redirect('users:user_selection')

@login_required
def upload_id_card(request):
    if request.method == 'POST':
        form = IdCardForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_id_card_uploaded = True
            user.save()

            if user.is_youth:
                return redirect('users:home_youth')
            else:
                return redirect('users:upload_land_register')
    else:
        form = IdCardForm(instance=request.user)

    return render(request, 'users/upload_id_card.html', {'form': form})

@login_required
def upload_land_register(request):
    user = request.user
    if user.is_superuser or user.is_youth:
        return redirect('users:home_youth')

    if request.method == 'POST':
        form = LandRegisterForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_land_register_uploaded = True
            user.save()
            return redirect('users:home_senior')
    else:
        form = LandRegisterForm(instance=user)

    return render(request, 'users/upload_land_register.html', {'form': form})