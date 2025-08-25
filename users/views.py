import json
import os
import re

import google.generativeai as genai
from formtools.wizard.views import SessionWizardView

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.http import JsonResponse

from django.db.models import Avg, Case, When, Q, IntegerField

from matching.utils import calculate_matching_score, get_matching_details, WEIGHTS
from matching.models import MoveInRequest
from room.models import Room
from review.models import Review
from .models import Region

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
from .models import User, CHOICE_PARTS, Region, Listing
from .models import get_choice_parts, important_points_parts

# ────────────────────────────────────────────────────────────────────────────
# Gemini 설정
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

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

# ────────────────────────────────────────────────────────────────────────────
# 최근 본 방 유틸
def _recent_rooms_from_session(request, limit: int = 20):
    """
    세션에 저장된 recent_room_ids(가장 최근이 앞쪽)를 읽어
    그 순서 그대로 정렬한 Room 목록을 반환.
    """
    ids = request.session.get("recent_room_ids", []) or []
    if not ids:
        return []
    preserved = Case(
        *[When(id=pk, then=pos) for pos, pk in enumerate(ids)],
        output_field=IntegerField(),
    )
    return list(Room.objects.filter(id__in=ids).order_by(preserved)[:limit])

# ────────────────────────────────────────────────────────────────────────────
# 설문 마법사
class SurveyWizard(SessionWizardView):
    def get_template_names(self):
        return ["users/survey_form.html"]

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        return context

    def post(self, request, *args, **kwargs):
        # '건너뛰기' 처리
        if "skip_step" in request.POST:
            current_form = self.get_form(data=self.request.POST, files=self.request.FILES)
            if current_form.is_valid():
                self.storage.set_step_data(self.steps.current, self.get_form_step_data(current_form))
            return self.done(self.get_form_list(), **kwargs)
        return super().post(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        form_data = self.get_all_cleaned_data()
        user = self.request.user

        # 값 있으면 반영(없으면 기존 유지)
        user.preferred_time = form_data.get("preferred_time", user.preferred_time)
        user.conversation_style = form_data.get("conversation_style", user.conversation_style)
        if "important_points" in form_data:
            selected_points = form_data.get("important_points", [])
            user.important_points = ",".join(selected_points)
        else:
            user.important_points = ""
        user.meal_preference = form_data.get("meal_preference", user.meal_preference)
        user.weekend_preference = form_data.get("weekend_preference", user.weekend_preference)
        user.smoking_preference = form_data.get("smoking_preference", user.smoking_preference)
        user.noise_level = form_data.get("noise_level", user.noise_level)
        user.space_sharing_preference = form_data.get("space_sharing_preference", user.space_sharing_preference)
        user.pet_preference = form_data.get("pet_preference", user.pet_preference)
        user.wishes = form_data.get("wishes", user.wishes)

        user.save()
        self.storage.reset()  # 세션 초기화

        return redirect("users:home_youth" if user.is_youth else "users:home_senior")


# ────────────────────────────────────────────────────────────────────────────
# 인증/로그인 관련
def user_selection(request):
    auth_logout(request)
    return render(request, "users/user_selection.html")


def login_as_user(request, user_type):
    user = None
    if user_type == "youth":
        user, _ = User.objects.get_or_create(username="김청년", defaults={"is_youth": True})
    elif user_type == "senior":
        user, _ = User.objects.get_or_create(username="박노인", defaults={"is_youth": False})

    if user:
        auth_logout(request)
        auth_login(request, user)
        request.session.cycle_key()
        print(f"로그인 성공: {user.username} (청년: {user.is_youth})")
        return redirect("users:user_info")
    else:
        return render(request, "users/user_selection.html", {"error_message": "사용자를 찾거나 생성할 수 없습니다."})


def user_info_view(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")

    user = request.user
    form = UserInformationForm(request.POST or None, instance=user)

    if request.method == "POST" and form.is_valid():
        form.save()
        if user.is_youth:
            return redirect("users:youth_region")
        else:
            return redirect("users:senior_living_type")

    return render(request, "users/user_info.html", {"form": form})


def youth_region_view(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if not request.user.is_youth:
        return render(request, "users/re_login.html")

    user = request.user
    form = YouthInterestedRegionForm(request.POST or None, instance=user)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:upload_id_card")

    return render(request, "users/youth_region.html", {"form": form})


def senior_living_type_view(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if request.user.is_youth:
        return render(request, "users/re_login.html")

    user = request.user
    form = SeniorLivingTypeForm(request.POST or None, instance=user)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:upload_id_card")

    return render(request, "users/senior_living_type.html", {"form": form})


def upload_id_card(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")

    user = request.user

    if request.method == "POST":
        form = IdCardForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_id_card_uploaded = True
            user.save()
            return redirect("users:survey_wizard_start")
    else:
        form = IdCardForm(instance=user)

    return render(request, "users/upload_id_card.html", {"form": form})


def user_logout(request):
    auth_logout(request)
    next_url = request.GET.get("next", "users:user_selection")
    return redirect(next_url)


# ────────────────────────────────────────────────────────────────────────────
# 청년 홈: AI 추천 + 최근 본 방 + (datalist 자동완성 후보)  — 캐시 차단
@never_cache
def home_youth(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if not request.user.is_youth:
        return render(request, "users/re_login.html")

    # 최근 본 방 (뒤로가기 시 즉시 반영)
    recent_rooms = _recent_rooms_from_session(request)

    # 🔽 자동완성 후보(rooms 데이터 기반으로 최대 300개 스캔 → 상위 50개만 노출)
    qs_for_suggest = (
        Room.objects
        .order_by("-id")
        .values("address_province", "address_city", "address_district", "nearest_subway")[:300]
    )
    seen, suggestions = set(), []

    def _add(x):
        x = (x or "").strip()
        if x and x not in seen:
            suggestions.append(x)
            seen.add(x)

    for r in qs_for_suggest:
        prov = r.get("address_province") or ""
        city = r.get("address_city") or ""
        dist = r.get("address_district") or ""
        sub = r.get("nearest_subway") or ""
        # 단일
        for v in (sub, dist, city, prov):
            _add(v)
        # 조합
        _add(" ".join(x for x in (city, dist) if x))
        _add(" ".join(x for x in (prov, city, dist) if x))

    # AI 입력 데이터
    data_for_ai = get_and_prepare_rooms_for_ai(request)

    # 데이터 없으면 빈 추천 + 최근 본 방만 렌더
    if not data_for_ai or not data_for_ai.get("available_rooms"):
        resp = render(request, "users/home_youth.html", {
            "recommended_rooms": [],
            "recent_rooms": recent_rooms,
            "region_suggestions": suggestions[:50],   # 🔽 datalist 후보
        })
        resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp["Pragma"] = "no-cache"
        resp["Expires"] = "0"
        return resp

    # Gemini 프롬프트
    prompt = f"""
        아래는 한 청년의 프로필과 관심 지역에 있는 여러 방의 정보(시니어의 프로필 포함)야.
        이 데이터들을 분석해서 청년과 가장 잘 맞는 순서대로 방 목록을 추천해 줘.

        **매칭 점수를 계산할 때 아래 항목의 중요도를 반드시 고려해.**
        - 반려동물 여부: 10
        - 흡연 여부: 10
        - 소음 허용도: 9
        - 활동 시간대: 8
        - 대화 빈도: 7
        - 생활 공간 중요 포인트: 6
        - 공용 공간 사용 빈도: 6
        - 식사 공유 여부: 5
        - 주말 생활 패턴: 4

        <청년 프로필>
        {json.dumps(data_for_ai['youth_profile'], indent=2, ensure_ascii=False)}

        <방 목록>
        {json.dumps(data_for_ai['available_rooms'], indent=2, ensure_ascii=False)}

        응답은 다음 JSON 형식으로만 제공해줘.
        ```json
        [
          {{"room_id":"<실제 ID>", "recommendation_reason":"<두 문장 이내>"}},
          {{"room_id":"<다른 ID>", "recommendation_reason":"<두 문장 이내>"}}
        ]
        ```
    """

    try:
        response = model.generate_content(prompt)
        if "```json" in response.text:
            response_text = response.text.split("```json")[1].split("```")[0]
        else:
            response_text = response.text
        recommended_list_from_ai = json.loads(response_text.strip())
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {e}")
        recommended_list_from_ai = []

    # 추천된 순서대로 Room 정렬
    sorted_rooms = []
    if isinstance(recommended_list_from_ai, list):
        room_map = {str(room.id): room for room in Room.objects.all()}
        for item in recommended_list_from_ai:
            room_id = str(item.get("room_id"))
            if room_id in room_map:
                room = room_map[room_id]
                room.recommendation_reason = item.get("recommendation_reason", "추천 이유가 제공되지 않았습니다.")
                sorted_rooms.append(room)

    # 세션에 추천/점수 저장 (전체목록 페이지에서 사용)
    ai_recommendations_with_score = {}
    for room in sorted_rooms:
        matching_score = calculate_matching_score(request.user, room.owner)
        ai_recommendations_with_score[str(room.id)] = {
            "reason": room.recommendation_reason,
            "score": matching_score,
        }
    request.session["ai_recommendations_with_score"] = ai_recommendations_with_score

    resp = render(request, "users/home_youth.html", {
        "recommended_rooms": sorted_rooms,
        "recent_rooms": recent_rooms,
        "region_suggestions": suggestions[:50],   # 🔽 datalist 후보
    })
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp["Pragma"] = "no-cache"
    resp["Expires"] = "0"
    return resp


def all_rooms_youth(request):
    if not request.user.is_authenticated or not request.user.is_youth:
        return redirect("users:user_login")

    ai_recommendations = request.session.get("ai_recommendations_with_score", {})

    recommended_rooms = []
    if ai_recommendations:
        room_ids = list(ai_recommendations.keys())
        rooms_from_db = Room.objects.filter(id__in=room_ids)
        room_map = {str(room.id): room for room in rooms_from_db}

        for room_id, data in ai_recommendations.items():
            room = room_map.get(room_id)
            if room:
                room.recommendation_reason = data["reason"]
                room.matching_score = data["score"]
                recommended_rooms.append(room)

    context = {"recommended_rooms": recommended_rooms}
    return render(request, "users/all_rooms_youth.html", context)


# ────────────────────────────────────────────────────────────────────────────
# 시니어 홈(자동완성 후보 포함)
def home_senior(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if request.user.is_youth:
        return render(request, "users/re_login.html")

    qs = (
        Room.objects
        .order_by("-id")
        .values("address_province", "address_city", "address_district", "nearest_subway")[:300]
    )

    seen, suggestions = set(), []

    def add(x):
        x = (x or "").strip()
        if x and x not in seen:
            suggestions.append(x)
            seen.add(x)

    for r in qs:
        prov = r.get("address_province") or ""
        city = r.get("address_city") or ""
        dist = r.get("address_district") or ""
        sub = r.get("nearest_subway") or ""

        # 단일 항목
        for v in (sub, dist, city, prov):
            add(v)
        # 조합
        add(" ".join(x for x in (city, dist) if x))
        add(" ".join(x for x in (prov, city, dist) if x))

    context = {"region_suggestions": suggestions[:50]}
    return render(request, "users/home_senior.html", context)


# ────────────────────────────────────────────────────────────────────────────
# 프로필/리뷰 관련
FIELD_LABELS = {
    "preferred_time": "생활리듬",
    "conversation_style": "대화스타일",
    "important_points": "중요한점",
    "noise_level": "소음수준",
    "meal_preference": "식사",
    "space_sharing_preference": "공간공유",
    "pet_preference": "반려동물",
    "smoking_preference": "흡연",
    "weekend_preference": "주말성향",
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


def _build_profile_parts(user_obj):
    if not user_obj:
        return None
    return {
        "preferred_time": get_choice_parts(user_obj, "preferred_time"),
        "conversation_style": get_choice_parts(user_obj, "conversation_style"),
        "important_points": important_points_parts(user_obj),
        "noise_level": get_choice_parts(user_obj, "noise_level"),
        "meal_preference": get_choice_parts(user_obj, "meal_preference"),
        "space_sharing_preference": get_choice_parts(user_obj, "space_sharing_preference"),
        "pet_preference": get_choice_parts(user_obj, "pet_preference"),
        "smoking_preference": get_choice_parts(user_obj, "smoking_preference"),
        "weekend_preference": get_choice_parts(user_obj, "weekend_preference"),
    }


def senior_profile(request, senior_id, room_id):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if not request.user.is_youth:
        return render(request, "users/re_login.html")

    owner = get_object_or_404(User, id=senior_id, is_youth=False)
    youth_user = request.user

    current_room = get_object_or_404(Room, id=room_id)
    is_land_register_verified = current_room.is_land_register_verified

    matching_details = get_matching_details(youth_user, owner)

    owner_parts = _build_profile_parts(owner)
    youth_parts = _build_profile_parts(youth_user)

    context = {
        "owner": owner,
        "youth_user": youth_user,
        "matching_score": matching_details["matching_score"],
        "matching_text": matching_details["matching_text"],
        "explanation": matching_details["explanation"],
        "hashtags": matching_details["hashtags"],
        "owner_is_id_card_uploaded": owner.is_id_card_uploaded,
        "is_land_register_verified": is_land_register_verified,
        "owner_parts": owner_parts,
        "youth_parts": youth_parts,
    }
    return render(request, "users/senior_profile.html", context)


def youth_profile(request, request_id):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if request.user.is_youth:
        return render(request, "users/re_login.html")

    move_in_request = get_object_or_404(
        MoveInRequest,
        id=request_id,
        room__owner=request.user,
    )

    senior_user = request.user
    youth_user = move_in_request.youth

    matching_score = calculate_matching_score(senior_user, youth_user)
    matching_details = get_matching_details(senior_user, youth_user)

    is_id_card_uploaded = youth_user.is_id_card_uploaded
    reviews = Review.objects.filter(target_youth=youth_user).order_by("-created_at")

    total_satisfaction_score = 0
    satisfaction_map = {
        "VERY_DISSATISFIED": 1, "DISSATISFIED": 2, "NORMAL": 3,
        "SATISFIED": 4, "VERY_SATISFIED": 5
    }
    for review in reviews:
        total_satisfaction_score += satisfaction_map.get(review.satisfaction, 0)

    average_rating = 0
    if reviews.count() > 0:
        average_rating = total_satisfaction_score / reviews.count()

    # 임시 AI 요약
    ai_summary = "시니어 다수가 이 청년의 생활 태도에 만족했습니다."
    good_hashtags = ["#깔끔한", "#활발함", "#규칙적인"]
    bad_hashtags = ["#깔끔한", "#활발함"]

    owner_parts = _build_profile_parts(senior_user)
    youth_parts = _build_profile_parts(youth_user)

    context = {
        "youth_user": youth_user,
        "senior_user": senior_user,
        "matching_score": matching_score,
        "matching_text": matching_details["matching_text"],
        "explanation": matching_details["explanation"],
        "hashtags": matching_details["hashtags"],
        "is_id_card_uploaded": is_id_card_uploaded,
        "reviews": reviews,
        "average_rating": round(average_rating, 1),
        "review_count": reviews.count(),
        "ai_summary": ai_summary,
        "good_hashtags": good_hashtags,
        "bad_hashtags": bad_hashtags,
        "owner_parts": owner_parts,
        "youth_parts": youth_parts,
    }
    return render(request, "users/youth_profile.html", context)


def all_reviews_for_youth(request, youth_id):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if request.user.is_youth:
        return render(request, "users/re_login.html")

    youth_user = get_object_or_404(User, id=youth_id)
    reviews = Review.objects.filter(target_youth=youth_user).order_by("-created_at")

    context = {"youth_user": youth_user, "reviews": reviews}
    return render(request, "users/all_reviews_for_youth.html", context)


def senior_info_view(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if request.user.is_youth:
        return render(request, "users/re_login.html")

    user = request.user

    user_preferences = []
    for field in [
        "preferred_time", "conversation_style", "meal_preference",
        "weekend_preference", "smoking_preference", "noise_level",
        "space_sharing_preference", "pet_preference",
    ]:
        field_value = getattr(user, field, None)
        if field_value:
            label = CHOICE_PARTS.get(field, {}).get(field_value, {}).get("label")
            if label:
                user_preferences.append(label)

    if user.important_points:
        important_points_codes = user.important_points.split(",")
        important_points_map = CHOICE_PARTS.get("important_points", {})
        for code in important_points_codes:
            label = important_points_map.get(code.strip().upper(), {}).get("label")
            if label:
                user_preferences.append(label)

    context = {
        "user": user,
        "living_type_display": user.get_living_type_display(),
        "user_preferences": user_preferences,
    }
    return render(request, "users/senior_info_view.html", context)


def youth_info_view(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if not request.user.is_youth:
        return render(request, "users/re_login.html")

    user = request.user
    user_preferences = []
    for field in [
        "preferred_time", "conversation_style", "meal_preference",
        "weekend_preference", "smoking_preference", "noise_level",
        "space_sharing_preference", "pet_preference",
    ]:
        field_value = getattr(user, field, None)
        if field_value:
            label = CHOICE_PARTS.get(field, {}).get(field_value, {}).get("label")
            if label:
                user_preferences.append(label)

    if user.important_points:
        important_points_codes = user.important_points.split(",")
        important_points_map = CHOICE_PARTS.get("important_points", {})
        for code in important_points_codes:
            cleaned_code = code.strip().upper()
            label = important_points_map.get(cleaned_code, {}).get("label")
            if label:
                user_preferences.append(label)

    context = {"user": user, "user_preferences": user_preferences}
    return render(request, "users/youth_info_view.html", context)


def my_reviews(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if not request.user.is_youth:
        return render(request, "users/re_login.html")

    user = request.user
    reviews = Review.objects.filter(target_youth=user).order_by("-created_at")

    context = {"youth_user": user, "reviews": reviews}
    return render(request, "users/my_reviews_for_youth.html", context)


def index(request):
    return redirect("users:user_selection")


# ────────────────────────────────────────────────────────────────────────────
# 자동완성 & 지역별 매물 API
@require_GET
def autocomplete_region(request):
    query = (request.GET.get("q") or request.GET.get("query") or "").strip()
    if not query:
        return JsonResponse({"results": []}, json_dumps_params={"ensure_ascii": False})

    regions = Region.objects.filter(name__icontains=query).values_list("name", flat=True)[:10]
    return JsonResponse({"results": list(regions)}, json_dumps_params={"ensure_ascii": False})


@require_GET
def listings_by_region(request):
    region_name = (request.GET.get("region") or "").strip()
    if not region_name:
        return JsonResponse({"results": []}, json_dumps_params={"ensure_ascii": False})

    listings = Listing.objects.filter(region__name=region_name).values("title", "price", "description")
    return JsonResponse({"results": list(listings)}, json_dumps_params={"ensure_ascii": False})


# ────────────────────────────────────────────────────────────────────────────
# AI 입력 데이터 준비
def get_and_prepare_rooms_for_ai(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if not request.user.is_youth:
        return render(request, "users/re_login.html")

    youth_user = request.user

    province = youth_user.interested_province
    city = youth_user.interested_city
    district = youth_user.interested_district

    if not province and not city and not district:
        return []

    filter_conditions = Q()
    if province:
        filter_conditions &= Q(address_province=province)
    if city:
        filter_conditions &= Q(address_city=city)
    if district:
        filter_conditions &= Q(address_district=district)

    filtered_rooms = Room.objects.filter(filter_conditions)

    ai_input_data = {
        "youth_profile": {
            "id": youth_user.id,
            "username": youth_user.username,
            "lifestyle": {
                "preferred_time": youth_user.preferred_time,
                "conversation_style": youth_user.conversation_style,
                "important_points": youth_user.important_points,
                "noise_level": youth_user.noise_level,
                "meal_preference": youth_user.meal_preference,
                "space_sharing_preference": youth_user.space_sharing_preference,
                "pet_preference": youth_user.pet_preference,
                "smoking_preference": youth_user.smoking_preference,
                "weekend_preference": youth_user.weekend_preference,
            },
        },
        "available_rooms": [],
    }

    for room in filtered_rooms:
        senior_owner = room.owner
        room_data = {
            "room_id": room.id,
            "rent_fee": room.rent_fee,
            "address": f"{room.address_province} {room.address_city} {room.address_district}",
            "senior_profile": {
                "id": senior_owner.id,
                "username": senior_owner.username,
                "lifestyle": {
                    "preferred_time": senior_owner.preferred_time,
                    "conversation_style": senior_owner.conversation_style,
                    "important_points": senior_owner.important_points,
                    "noise_level": senior_owner.noise_level,
                    "meal_preference": senior_owner.meal_preference,
                    "space_sharing_preference": senior_owner.space_sharing_preference,
                    "pet_preference": senior_owner.pet_preference,
                    "smoking_preference": senior_owner.smoking_preference,
                    "weekend_preference": senior_owner.weekend_preference,
                },
            },
        }
        ai_input_data["available_rooms"].append(room_data)

    print(f"청년 관심 지역: {province}, {city}, {district}")
    print(f"필터링된 방 개수: {filtered_rooms.count()}")

    return ai_input_data
