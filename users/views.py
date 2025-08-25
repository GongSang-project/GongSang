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
from django.db.models import Case, When, IntegerField

import os
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache

from room.views_register import _load_addr_tree, _get_addr_error

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import IdCardForm
from .models import User
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

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

try:
    from room.models import RoomPhoto
except Exception:
    RoomPhoto = None

# ────────────────────────────────────────────────────────────────────────────
# 최근 본 방 유틸
def _recent_rooms_from_session(request, limit: int = 20):
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
    addr_tree = _load_addr_tree()
    addr_tree_json = json.dumps(addr_tree, ensure_ascii=False)
    error = None

    form = YouthInterestedRegionForm(request.POST or None, instance=user)

    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data
            s = data.get("interested_province")
            g = data.get("interested_city")
            d = data.get("interested_district")

            # 주소 트리를 사용하여 유효성 검사
            ok = bool(s in addr_tree and g in addr_tree.get(s, {}) and d in addr_tree.get(s, {}).get(g, []))

            if not ok:
                error = "유효한 행정동을 선택해 주세요."
            else:
                form.save()
                return redirect("users:upload_id_card")
    else:
        form = YouthInterestedRegionForm(instance=user)

    return render(
        request,
        "users/youth_region.html",
        {
            "form": form,
            "addr_tree_json": addr_tree_json,
            "error": error,
        },
    )


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

ENCRYPTION_KEY = settings.ENCRYPTION_KEY

def encrypt_image(image_file):
    try:
        image_data = image_file.read()

        padded_data = pad(image_data, AES.block_size)

        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
        encrypted_data = cipher.encrypt(padded_data)

        return base64.b64encode(cipher.iv + encrypted_data)
    except Exception as e:
        print(f"암호화 오류: {e}")
        return None

def upload_id_card(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")

    user = request.user

    if request.method == "POST":
        form = IdCardForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            uploaded_file = request.FILES.get('id_card_image')

            if uploaded_file:
                encrypted_data = encrypt_image(uploaded_file)

                if encrypted_data:
                    user.id_card_image = encrypted_data
                    user.is_id_card_uploaded = True
                    user.save()

                    return redirect("users:survey_wizard_start")
                else:
                    # 암호화 실패 시 에러 처리
                    form.add_error(None, "파일 암호화 중 오류가 발생했습니다.")
    else:
        form = IdCardForm(instance=user)

    return render(request, "users/upload_id_card.html", {"form": form})


def user_logout(request):
    auth_logout(request)
    next_url = request.GET.get("next", "users:user_selection")
    return redirect(next_url)


# ────────────────────────────────────────────────────────────────────────────
# 청년 홈: AI 추천 + 최근 본 방 + (datalist 자동완성 후보) — 캐시 차단
@never_cache
def home_youth(request):
    if not request.user.is_authenticated:
        return render(request, "users/re_login.html")
    if not request.user.is_youth:
        return render(request, "users/re_login.html")

    recent_rooms = _recent_rooms_from_session(request)

    qs_for_suggest = (
        Room.objects
        .order_by("-id")
        .values("address_province", "address_city", "address_district", "nearest_subway")[:300]
    )
    seen, suggestions = set(), []
    def _add(x):
        x = (x or "").strip()
        if x and x not in seen:
            suggestions.append(x); seen.add(x)
    for r in qs_for_suggest:
        prov = r.get("address_province") or ""
        city = r.get("address_city") or ""
        dist = r.get("address_district") or ""
        sub  = r.get("nearest_subway") or ""
        for v in (sub, dist, city, prov): _add(v)
        _add(" ".join(x for x in (city, dist) if x))
        _add(" ".join(x for x in (prov, city, dist) if x))

    data_for_ai = get_and_prepare_rooms_for_ai(request)
    if not data_for_ai or not data_for_ai.get("available_rooms"):
        resp = render(request, "users/home_youth.html", {
            "recommended_rooms": [],
            "recent_rooms": recent_rooms,
            "region_suggestions": suggestions[:50],
        })
        resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp["Pragma"] = "no-cache"; resp["Expires"] = "0"
        return resp

    prompt = f""" ... 그대로 ... """

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

    # ✅ 여기만 바꿈: 사진을 함께 prefetch해서 카드 썸네일에서 바로 사용 가능
    sorted_rooms = []
    if isinstance(recommended_list_from_ai, list):
        room_qs = Room.objects.all()
        if RoomPhoto:
            room_qs = room_qs.prefetch_related("room_photos")  # ← 핵심
        room_map = {str(room.id): room for room in room_qs}

        for item in recommended_list_from_ai:
            room_id = str(item.get("room_id"))
            if room_id in room_map:
                room = room_map[room_id]
                room.recommendation_reason = item.get("recommendation_reason", "추천 이유가 제공되지 않았습니다.")
                sorted_rooms.append(room)

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
        "region_suggestions": suggestions[:50],
    })
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp["Pragma"] = "no-cache"; resp["Expires"] = "0"
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

    ai_summary = "아직 등록된 후기가 없거나, AI 요약 생성에 필요한 데이터가 부족합니다."
    good_hashtags = []
    bad_hashtags = []

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

    review_texts_list = []
    for review in reviews:
        if review.good_points:
            review_texts_list.append(review.good_points)
        if review.bad_points:
            review_texts_list.append(review.bad_points)

    review_texts = " ".join(review_texts_list)

    if review_texts:
        prompt = f"""
                아래 후기 텍스트들을 분석하여 전체 내용을 50자 이내로 간결하게 요약해줘.
                요약 내용은 그저 나열식이 아니라 깔끔하게 정리된 문장이어야 해. 존댓말을 사용해.
                그리고 후기에서 긍정적인 내용과 부정적인 내용을 각각 3개의 해시태그로 추출해줘.

                <후기 텍스트>
                "{review_texts}"

                응답은 다음 JSON 형식으로만 제공해줘. 해시태그는 한글로.
                ```json
                {{
                    "summary": "<간결한 요약>",
                    "good_hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"],
                    "bad_hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"]
                }}
                ```
            """
        try:
            response = model.generate_content(prompt)
            if "```json" in response.text:
                response_text = response.text.split("```json")[1].split("```")[0]
            else:
                response_text = response.text
            ai_data = json.loads(response_text.strip())

            ai_summary = ai_data.get('summary', ai_summary)
            good_hashtags = ai_data.get('good_hashtags', good_hashtags)
            bad_hashtags = ai_data.get('bad_hashtags', bad_hashtags)

        except Exception as e:
            print(f"Gemini API 호출 중 오류 발생: {e}")


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
