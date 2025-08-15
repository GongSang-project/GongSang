from django.urls import reverse
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
    YouthUserInformationForm,
    SeniorUserInformationForm,
    IdCardForm,
    LandRegisterForm,
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

REQUIRED_FIELDS = {
    'basic_info': ['username', 'age', 'gender'],
    'senior_specific': ['living_type'],
    'id_card': ['is_id_card_uploaded'],
    'survey': [
        'preferred_time', 'conversation_style', 'important_points', 'meal_preference',
        'weekend_preference', 'smoking_preference', 'noise_level', 'space_sharing_preference',
        'pet_preference',
    ],
    'region': []
}

class SurveyWizard(SessionWizardView):
    def get_template_names(self):
        return ['users/survey_form.html']

    def get_step_url(self, step):
        return reverse('users:survey_wizard_url', args=[step])

    # get 요청을 처리하여 미완료된 설문 페이지로 리디렉션
    def get(self, request, *args, **kwargs):
        user = request.user

        is_survey_complete = all(getattr(user, field, None) for field in REQUIRED_FIELDS['survey'])
        if is_survey_complete:
            return redirect('users:check_user_progress')

        # 미완료된 설문이 있을 경우, 처음 미완료된 단계로 리디렉션
        first_empty_db_field_step = None
        for i, field_name in enumerate(REQUIRED_FIELDS['survey']):
            if not getattr(user, field_name):
                first_empty_db_field_step = FORMS[i][0]
                break

        if first_empty_db_field_step:
            first_empty_db_index = self.steps.all.index(first_empty_db_field_step)
            current_step_index = self.steps.all.index(self.steps.current)

            if current_step_index > first_empty_db_index:
                return redirect(reverse('users:survey_wizard_url', args=[first_empty_db_field_step]))

        return super().get(request, *args, **kwargs)


        # if not user.is_authenticated:
        #     return redirect('users:user_selection')
        #
        # current_step_name = self.steps.current
        #
        # survey_fields = [
        #     'preferred_time', 'conversation_style', 'important_points', 'meal_preference',
        #     'weekend_preference', 'smoking_preference', 'noise_level', 'space_sharing_preference',
        #     'pet_preference',
        # ]
        #
        # first_empty_db_field_step = None
        # for i, field_name in enumerate(survey_fields):
        #     if not getattr(user, field_name):
        #         first_empty_db_field_step = FORMS[i][0]
        #         break
        #
        # if not first_empty_db_field_step:
        #     if user.is_youth:
        #         return redirect('users:home_youth')
        #     else:
        #         return redirect('users:home_senior')
        #
        # if first_empty_db_field_step:
        #     first_empty_db_index = self.steps.all.index(first_empty_db_field_step)
        #     current_step_index = self.steps.all.index(current_step_name)
        #
        #     if current_step_index > first_empty_db_index:
        #         return redirect(reverse('users:survey_wizard_url', args=[first_empty_db_field_step]))
        #
        # return super().get(request, *args, **kwargs)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        return context

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

        return redirect('users:check_user_progress')

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
        auth_logout(request)
        auth_login(request, user)
        request.session.cycle_key()

        print(f"로그인 성공: {user.username} (청년: {user.is_youth})")

        return redirect('users:check_user_progress')
    else:
        return render(request, 'users/user_selection.html', {'error_message': '사용자를 찾거나 생성할 수 없습니다.'})


@login_required
def check_user_progress(request):
    user = request.user

    # 1. 기본 정보 확인
    required_fields_list = REQUIRED_FIELDS['basic_info']
    if not user.is_youth:  # 시니어인 경우 동거 형태 필드 추가
        required_fields_list += REQUIRED_FIELDS['senior_specific']

    is_basic_info_complete = all(getattr(user, field, None) for field in required_fields_list)
    print(f"기본 정보 완료 여부: {is_basic_info_complete}")
    if not is_basic_info_complete:
        print("기본 정보가 불완전하여 user_info 페이지로 리디렉션합니다.")
        return redirect('users:user_info')

    # 2. 신분증 첨부 확인 (시니어 회원만 해당)
    if not user.is_id_card_uploaded:
        return redirect('users:upload_id_card')

    # 3. 성향 조사 확인
    is_survey_complete = all(getattr(user, field, None) for field in REQUIRED_FIELDS['survey'])
    if not is_survey_complete:
        return redirect(reverse('users:survey_wizard_url', args=[FORMS[0][0]]))

    # 4. 지역 조사 확인 (청년 회원만)
    # 현재는 필수 필드가 없으므로 건너뜀.
    # 추후 지역 선택 필드가 추가되면 로직 추가
    # if user.is_youth and not user.is_region_selected:
    #     return redirect('users:region_survey')

    # 모든 단계를 완료했다면 홈으로 이동
    if user.is_youth:
        return redirect('users:home_youth')
    else:
        return redirect('users:home_senior')

@login_required
def user_info_view(request):
    user = request.user

    required_fields_list = REQUIRED_FIELDS['basic_info']
    if not user.is_youth:
        required_fields_list += REQUIRED_FIELDS['senior_specific']

    is_basic_info_complete = all(getattr(user, field, None) for field in required_fields_list)

    if is_basic_info_complete:
        return redirect('users:check_user_progress')

    FormClass = YouthUserInformationForm if user.is_youth else SeniorUserInformationForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save()
            request.user.refresh_from_db()

            return redirect('users:check_user_progress')
    else:
        form = FormClass(instance=user)

    return render(request, 'users/user_info.html', {'form': form})

@login_required
def upload_id_card(request):
    user = request.user

    if request.method == 'POST':
        form = IdCardForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_id_card_uploaded = True
            user.save()
            return redirect('users:check_user_progress') # 다음 단계 확인 로직으로 이동
    else:
        form = IdCardForm(instance=user)

    return render(request, 'users/upload_id_card.html', {'form': form})


@login_required
def region_survey(request):
    user = request.user
    if not user.is_youth:
        return redirect('users:check_user_progress')

    if request.method == 'POST':
        # 임시 로직, 추후 지역 저장 로직 추가
        return redirect('users:check_user_progress')

    return render(request, 'users/region_survey.html')

def user_logout(request):
    auth_logout(request)
    next_url = request.GET.get('next', 'users:user_selection')
    return redirect(next_url)

def home_youth(request):
    return render(request, 'users/home_youth.html')

def home_senior(request):
    return render(request, 'users/home_senior.html')

@login_required
def upload_land_register(request):
    user = request.user
    if user.is_youth:
        return redirect('users:check_user_progress')

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