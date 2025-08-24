from django.contrib.auth.decorators import login_required
from formtools.wizard.views import SessionWizardView
from django.shortcuts import redirect, render, get_object_or_404
from matching.utils import calculate_matching_score, get_matching_details, WEIGHTS
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
from .models import User, CHOICE_PARTS
from django.contrib.auth import login as auth_login, logout as auth_logout
from matching.models import MoveInRequest
from room.models import Room
from review.models import Review
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from .models import Region, Listing
import re

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
    auth_logout(request)
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
    # 최근 등록 방에서 주소/역 이름을 뽑아 후보 생성 (JS 없이 datalist용)
    qs = (
        Room.objects
        .order_by('-id')
        .values('address_province', 'address_city', 'address_district', 'nearest_subway')[:300]
    )

    seen, suggestions = set(), []
    def add(x):
        x = (x or '').strip()
        if x and x not in seen:
            suggestions.append(x)
            seen.add(x)

    for r in qs:
        prov = r.get('address_province') or ''
        city = r.get('address_city') or ''
        dist = r.get('address_district') or ''
        sub  = r.get('nearest_subway') or ''

        # 단일 항목
        for v in (sub, dist, city, prov):
            add(v)

        # 조합(시군구/시도 시군구 동)
        add(" ".join(x for x in (city, dist) if x))
        add(" ".join(x for x in (prov, city, dist) if x))

    context = {
        'region_suggestions': suggestions[:50],  # 너무 많으면 UX 나빠짐
    }
    return render(request, 'users/home_senior.html', context)


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
        "preferred_time": get_choice_parts(user_obj, "preferred_time"),
        "conversation_style": get_choice_parts(user_obj, "conversation_style"),
        "important_points": important_points_parts(user_obj),  # 리스트
        "noise_level": get_choice_parts(user_obj, "noise_level"),
        "meal_preference": get_choice_parts(user_obj, "meal_preference"),
        "space_sharing_preference": get_choice_parts(user_obj, "space_sharing_preference"),
        "pet_preference": get_choice_parts(user_obj, "pet_preference"),
        "smoking_preference": get_choice_parts(user_obj, "smoking_preference"),
        "weekend_preference": get_choice_parts(user_obj, "weekend_preference"),
    }

def senior_profile(request, senior_id, room_id):
    # 매칭 대상 시니어 유저 객체
    owner = get_object_or_404(User, id=senior_id, is_youth=False)
    youth_user = request.user

    # 현재 보고 있는 방의 등기부 등본 인증 여부
    current_room = get_object_or_404(Room, id=room_id)
    is_land_register_verified = current_room.is_land_register_verified

    # 매칭 상세 정보 가져오기
    matching_details = get_matching_details(youth_user, owner)

    owner_parts = _build_profile_parts(owner)
    youth_parts = _build_profile_parts(youth_user)

    context = {
        'owner': owner,
        'youth_user': youth_user,
        'matching_score': matching_details['matching_score'],
        'matching_text': matching_details['matching_text'],
        'explanation': matching_details['explanation'],
        'hashtags': matching_details['hashtags'],
        'owner_is_id_card_uploaded': owner.is_id_card_uploaded,
        'is_land_register_verified': is_land_register_verified,

        'owner_parts': owner_parts,
        'youth_parts': youth_parts,
    }
    return render(request, 'users/senior_profile.html', context)


@login_required
def youth_profile(request, request_id):
    if request.user.is_youth:
        return redirect('users:home_youth')

    move_in_request = get_object_or_404(
        MoveInRequest,
        id=request_id,
        room__owner=request.user
    )

    senior_user = request.user
    youth_user = move_in_request.youth

    # 매칭 점수 및 상세 분석 결과 계산
    matching_score = calculate_matching_score(senior_user, youth_user)
    matching_details = get_matching_details(senior_user, youth_user)

    is_id_card_uploaded = youth_user.is_id_card_uploaded

    # 데이터베이스에서 해당 청년에 대한 후기 가져오기
    reviews = Review.objects.filter(target_youth=youth_user).order_by('-created_at')

    # 별점 평균 계산
    total_satisfaction_score = 0
    satisfaction_map = {
        'VERY_DISSATISFIED': 1, 'DISSATISFIED': 2, 'NORMAL': 3,
        'SATISFIED': 4, 'VERY_SATISFIED': 5
    }
    for review in reviews:
        total_satisfaction_score += satisfaction_map.get(review.satisfaction, 0)

    average_rating = 0
    if reviews.count() > 0:
        average_rating = total_satisfaction_score / reviews.count()

    # 추후 실제 AI 기능으로 대체, 임시 데이터
    ai_summary = "시니어 다수가 이 청년의 생활 태도에 만족했습니다."
    good_hashtags = ["#깔끔한", "#활발함", "#규칙적인"]
    bad_hashtags = ["#깔끔한", "#활발함"]

    # 프론트에서 추가
    owner_parts = _build_profile_parts(senior_user)   
    youth_parts = _build_profile_parts(youth_user) 

    context = {
        'youth_user': youth_user,
        'senior_user': senior_user,
        'matching_score': matching_score,
        'matching_text': matching_details['matching_text'],
        'explanation': matching_details['explanation'],
        'hashtags': matching_details['hashtags'],
        'is_id_card_uploaded': is_id_card_uploaded,

        'reviews': reviews,
        'average_rating': round(average_rating, 1),
        'review_count': reviews.count(),
        'ai_summary': ai_summary,
        'good_hashtags': good_hashtags,
        'bad_hashtags': bad_hashtags,

        'owner_parts': owner_parts,
        'youth_parts': youth_parts,
    }

    return render(request, 'users/youth_profile.html', context)


def all_reviews_for_youth(request, youth_id):
    youth_user = get_object_or_404(User, id=youth_id)
    reviews = Review.objects.filter(youth=youth_user).order_by('-created_at')

    context = {
        'youth_user': youth_user,
        'reviews': reviews
    }
    return render(request, 'users/all_reviews_for_youth.html', context)

def senior_info_view(request):
    user = request.user

    if user.is_youth:
        return render(request, 'users/re_login.html')

    user_preferences = []
    for field in [
        'preferred_time', 'conversation_style', 'meal_preference',
        'weekend_preference', 'smoking_preference', 'noise_level',
        'space_sharing_preference', 'pet_preference'
    ]:
        field_value = getattr(user, field, None)
        if field_value:
            label = CHOICE_PARTS.get(field, {}).get(field_value, {}).get('label')
            if label:
                user_preferences.append(label)

    if user.important_points:
        important_points_codes = user.important_points.split(',')
        important_points_map = CHOICE_PARTS.get('important_points', {})
        for code in important_points_codes:
            label = important_points_map.get(code.strip().upper(), {}).get('label')
            if label:
                user_preferences.append(label)

    context = {
        'user': user,
        'living_type_display': user.get_living_type_display(),
        'user_preferences': user_preferences,
    }

    return render(request, 'users/senior_info_view.html', context)

def youth_info_view(request):
    user = request.user

    if not user.is_youth:
        return render(request, 'users/re_login.html')

    user_preferences = []
    for field in [
        'preferred_time', 'conversation_style', 'meal_preference',
        'weekend_preference', 'smoking_preference', 'noise_level',
        'space_sharing_preference', 'pet_preference'
    ]:
        field_value = getattr(user, field, None)
        if field_value:
            label = CHOICE_PARTS.get(field, {}).get(field_value, {}).get('label')
            if label:
                user_preferences.append(label)

    if user.important_points:
        important_points_codes = user.important_points.split(',')
        important_points_map = CHOICE_PARTS.get('important_points', {})
        for code in important_points_codes:
            cleaned_code = code.strip().upper()
            label = important_points_map.get(cleaned_code, {}).get('label')
            if label:
                user_preferences.append(label)

    context = {
        'user': user,
        'user_preferences': user_preferences,
    }

    return render(request, 'users/youth_info_view.html', context)

@login_required
def my_reviews(request):
    user = request.user

    if not user.is_youth:
        return render(request, 'users/re_login.html')

    # 로그인한 청년 사용자의 ID로 후기 필터링
    reviews = Review.objects.filter(target_youth=user).order_by('-created_at')

    context = {
        'youth_user': user,
        'reviews': reviews
    }
    return render(request, 'users/all_reviews_for_youth.html', context)

def index(request):
    return redirect('users:user_selection')


# 검색 자동완성
@require_GET
def autocomplete_region(request):
    query = (request.GET.get("q") or request.GET.get("query") or "").strip()
    if not query:
        return JsonResponse({"results": []}, json_dumps_params={'ensure_ascii': False})

    regions = Region.objects.filter(name__icontains=query)\
                            .values_list("name", flat=True)[:10]
    return JsonResponse({"results": list(regions)}, json_dumps_params={'ensure_ascii': False})

@require_GET
def listings_by_region(request):
    region_name = (request.GET.get("region") or "").strip()
    if not region_name:
        return JsonResponse({"results": []}, json_dumps_params={'ensure_ascii': False})

    listings = Listing.objects.filter(region__name=region_name)\
                              .values("title", "price", "description")
    return JsonResponse({"results": list(listings)}, json_dumps_params={'ensure_ascii': False})