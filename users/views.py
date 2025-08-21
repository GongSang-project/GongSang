from django.urls import reverse
from django.contrib.auth.decorators import login_required
from formtools.wizard.views import SessionWizardView
from django.shortcuts import redirect, render, get_object_or_404
from matching.utils import calculate_matching_score, WEIGHTS
from .forms import (
    UserInformationForm,
    SeniorLivingTypeForm,
    IdCardForm,
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
    YouthInterestedRegionForm,
)
from .models import User
from room.models import Room
from django.contrib.auth import login as auth_login, logout as auth_logout

# 프론트에서 추가: 맵핑 임포트
from .models import get_choice_parts, important_points_parts 

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
        if 'important_points' in form_data:
            selected_points = form_data.get('important_points', [])
            user.important_points = ','.join(selected_points)
        else:
            user.important_points = ''
        user.meal_preference = form_data.get('meal_preference', user.meal_preference)
        user.weekend_preference = form_data.get('weekend_preference', user.weekend_preference)
        user.smoking_preference = form_data.get('smoking_preference', user.smoking_preference)
        user.noise_level = form_data.get('noise_level', user.noise_level)
        user.space_sharing_preference = form_data.get('space_sharing_preference', user.space_sharing_preference)
        user.pet_preference = form_data.get('pet_preference', user.pet_preference)
        user.wishes = form_data.get('wishes', user.wishes)

        user.save()
        self.storage.reset()  # 세션 데이터 초기화

        return redirect('users:home_youth' if user.is_youth else 'users:home_senior')

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
        return redirect('users:user_info')
    else:
        return render(request, 'users/user_selection.html', {'error_message': '사용자를 찾거나 생성할 수 없습니다.'})


@login_required
def user_info_view(request):
    user = request.user
    form = UserInformationForm(request.POST or None, instance=user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        if user.is_youth:
            return redirect('users:youth_region')
        else:
            return redirect('users:senior_living_type')

    return render(request, 'users/user_info.html', {'form': form})

@login_required
def youth_region_view(request):
    user = request.user
    form = YouthInterestedRegionForm(request.POST or None, instance=user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('users:upload_id_card')

    return render(request, 'users/youth_region.html', {'form': form})

@login_required
def senior_living_type_view(request):
    user = request.user
    form = SeniorLivingTypeForm(request.POST or None, instance=user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('users:upload_id_card')

    return render(request, 'users/senior_living_type.html', {'form': form})

@login_required
def upload_id_card(request):
    user = request.user

    if request.method == 'POST':
        form = IdCardForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_id_card_uploaded = True
            user.save()
            return redirect('users:survey_wizard_start')
    else:
        form = IdCardForm(instance=user)

    return render(request, 'users/upload_id_card.html', {'form': form})

def user_logout(request):
    auth_logout(request)
    next_url = request.GET.get('next', 'users:user_selection')
    return redirect(next_url)

def home_youth(request):
    return render(request, 'users/home_youth.html')

def home_senior(request):
    return render(request, 'users/home_senior.html')




FIELD_LABELS = {
    'preferred_time': '생활리듬',
    'conversation_style': '대화스타일',
    'important_points': '중요한점',
    'noise_level': '소음수준',
    'meal_preference': '식사',
    'space_sharing_preference': '공간공유',
    'pet_preference': '반려동물',
    'smoking_preference': '흡연',
    'weekend_preference': '주말성향',
}

def get_matching_text(score):
    if score >= 90:
        return "매우 잘 맞음 👍"
    elif score >= 70:
        return "잘 맞음 😊"
    elif score >= 50:
        return "보통 😐"
    else:
        return "조금 다름 🧐"
    
# 프론트에서 추가: 사용자에 대해 emoji/label을 하나로

def _build_profile_parts(user_obj):
    if not user_obj:
        return None
    return {
        "preferred_time":            get_choice_parts(user_obj, "preferred_time"),
        "conversation_style":        get_choice_parts(user_obj, "conversation_style"),
        "important_points":          important_points_parts(user_obj),  # 리스트
        "noise_level":               get_choice_parts(user_obj, "noise_level"),
        "meal_preference":           get_choice_parts(user_obj, "meal_preference"),
        "space_sharing_preference":  get_choice_parts(user_obj, "space_sharing_preference"),
        "pet_preference":            get_choice_parts(user_obj, "pet_preference"),
        "smoking_preference":        get_choice_parts(user_obj, "smoking_preference"),
        "weekend_preference":        get_choice_parts(user_obj, "weekend_preference"),
    }

def senior_profile(request, senior_id, room_id):
    # 매칭 대상 시니어 유저 객체
    owner = get_object_or_404(User, id=senior_id, is_youth=False)
    youth_user = request.user

    # 현재 보고 있는 방의 등기부 등본 인증 여부
    current_room = get_object_or_404(Room, id=room_id)
    is_land_register_verified = current_room.is_land_register_verified

    # 매칭 점수 계산
    matching_score = calculate_matching_score(youth_user, owner)
    # 점수 구간별 매칭 문구 생성
    matching_text = get_matching_text(matching_score)

    # 1. 일치하는 항목 중 가중치가 높은 상위 2개 찾기
    matched_fields = {}

    # 필드 일치 여부 확인
    for field in WEIGHTS:
        # important_points는 특별 처리 (다중 선택)
        if field == 'important_points':
            youth_points = set(youth_user.important_points.split(',')) if youth_user.important_points else set()
            owner_points = set(owner.important_points.split(',')) if owner.important_points else set()
            match_count = len(youth_points.intersection(owner_points))
            if match_count > 0:
                matched_fields['important_points'] = WEIGHTS['important_points']
            continue

        # 소음 수준은 차이가 0일 때 일치로 간주
        if field == 'noise_level':
            if youth_user.noise_level == owner.noise_level:
                matched_fields['noise_level'] = WEIGHTS['noise_level']
            continue

        # 기타 단일 선택 항목
        if getattr(youth_user, field) == getattr(owner, field):
            matched_fields[field] = WEIGHTS[field]

    # 가중치가 높은 순서로 정렬하여 상위 2개 항목 추출
    top_matches = sorted(matched_fields, key=lambda f: WEIGHTS[f], reverse=True)[:2]

    # 설명 문구 생성
    top_match_names = [FIELD_LABELS[f] for f in top_matches]
    explanation = f"'{top_match_names[0]}'과 '{top_match_names[1]}'이 잘 맞아요." if len(top_match_names) >= 2 else ""

    # 2. 잘 맞는 해시태그 3가지 생성
    hashtags = []

    # 활동 시간대
    if youth_user.preferred_time == owner.preferred_time:
        if youth_user.preferred_time == 'A':
            hashtags.append('아침형')
        else:
            hashtags.append('저녁형')

    # 대화 스타일
    if youth_user.conversation_style == owner.conversation_style:
        if youth_user.conversation_style == 'A':
            hashtags.append('조용함')
        else:
            hashtags.append('활발함')

    # 중요한 점 (다중 선택)
    youth_points = set(youth_user.important_points.split(',')) if youth_user.important_points else set()
    owner_points = set(owner.important_points.split(',')) if owner.important_points else set()
    for choice in youth_points.intersection(owner_points):
        if choice == 'A':
            hashtags.append('깔끔한')
        elif choice == 'B':
            hashtags.append('생활리듬')
        elif choice == 'C':
            hashtags.append('소통')
        elif choice == 'D':
            hashtags.append('배려심')
        else:
            hashtags.append('사생활존중')

    # 식사
    if youth_user.meal_preference == owner.meal_preference:
        if youth_user.meal_preference == 'A':
            hashtags.append('함께식사')
        else:
            hashtags.append('각자식사')

    # 주말
    if youth_user.weekend_preference == owner.weekend_preference:
        if youth_user.weekend_preference == 'A':
            hashtags.append('집콕')
        else:
            hashtags.append('외출')

    # 흡연
    if youth_user.smoking_preference == owner.smoking_preference:
        if youth_user.smoking_preference == 'A':
            hashtags.append('흡연')
        else:
            hashtags.append('비흡연')

    # 소음 발생
    if youth_user.noise_level == owner.noise_level:
        if youth_user.noise_level == 'A':
            hashtags.append('소음가능')
        elif youth_user.noise_level == 'B':
            hashtags.append('소음일부가능')
        else:
            hashtags.append('소음불가')

    # 공간 공유
    if youth_user.space_sharing_preference == owner.space_sharing_preference:
        if youth_user.space_sharing_preference == 'A':
            hashtags.append('공용활발')
        elif youth_user.space_sharing_preference == 'B':
            hashtags.append('공용적당')
        else:
            hashtags.append('공용적음')

    # 반려동물
    if youth_user.pet_preference == owner.pet_preference:
        if youth_user.pet_preference == 'A':
            hashtags.append('반려동물과')
        else:
            hashtags.append('반려동물없이')

    # 중복 제거 및 최대 3개만 선택
    hashtags = list(dict.fromkeys(hashtags))[:3]

    # 등기부 등본 인증 여부
    is_land_register_verified = False
    if owner.owned_rooms.exists():
        first_room = owner.owned_rooms.first()
        is_land_register_verified = first_room.is_land_register_verified

    owner_parts = _build_profile_parts(owner)
    youth_parts = _build_profile_parts(youth_user)

    context = {
        'owner': owner,
        'youth_user': youth_user,
        'matching_score': matching_score,
        'matching_text': matching_text,
        'explanation': explanation,
        'hashtags': hashtags,
        'owner_is_id_card_uploaded': owner.is_id_card_uploaded,
        'is_land_register_verified': is_land_register_verified,

        'owner_parts': owner_parts,
        'youth_parts': youth_parts,
    }
    return render(request, 'users/senior_profile.html', context)