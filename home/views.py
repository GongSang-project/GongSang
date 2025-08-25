from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Region, Listing
from room.models import Room
from django.views.decorators.cache import never_cache

from django.db.models import (Case, When, Value, IntegerField, F, Q,)

"""
def home_view(request):
    # 최근 본 방 ID 목록(가장 최근이 앞쪽)
    ids = request.session.get("recent_room_ids", [])

    recent_rooms = []
    if ids:
        # ids 순서를 그대로 유지해서 정렬
        preserved = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(ids)])
        recent_rooms = list(Room.objects.filter(id__in=ids).order_by(preserved))

    # 첫 진입 추천(임시: 최신순 상위 8개)
    rooms = Room.objects.order_by("-created_at")[:8]
    categories = ["아파트", "빌라", "오피스텔", "주택"]

    return render(
        request,
        "home/home.html",
        {
            "rooms": rooms,
            "categories": categories,
            "recent_rooms": recent_rooms,
        },
    )
"""

@never_cache
def home_view(request):
    """
    - 상단: AI 추천(= match_score 순 상위 8개)
    - 하단: 최근 본 방 (session 저장된 recent_room_ids 순서 유지)
    """

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')
    if not getattr(request.user, "is_youth", False):
        return render(request, 'users/re_login.html')

    # 추천
    if request.user.is_authenticated and getattr(request.user, "is_youth", False):
        recommended_rooms = _recommend_queryset_for(request.user)[:8]
    else:
        # 비로그인/시니어는 최신순 fallback
        recommended_rooms = Room.objects.order_by("-created_at")[:8]

    # 최근 본 방
    ids = request.session.get("recent_room_ids", [])
    recent_rooms = []
    if ids:
        # ids의 순서를 유지하려면 Case/When으로 정렬 인덱스 부여
        preserved = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(ids)], output_field=IntegerField())
        recent_rooms = list(Room.objects.filter(id__in=ids).order_by(preserved))

    categories = ["아파트", "빌라", "오피스텔", "주택"]

    resp = render(
        request,
        "home/home.html",
        {
            "rooms": recommended_rooms,   # ← 템플릿의 "AI가 추천…" 섹션에서 사용
            "categories": categories,
            "recent_rooms": recent_rooms,
        },
    )
    resp["Cache-Control"] = "no-store"  # 뒤로가기 시 캐시 잔상 방지
    return resp

# ORM 기반 방 추천
# 가중치(숫자만 조정)
WEIGHTS = {
    "region_province": 5,   # 시/도
    "region_city": 8,       # 시/군/구
    "region_district": 12,  # 읍/면/동
    "pet_yes": 8,           # 유저가 반려동물 가능(A)이고 방이 허용(True)
    "pet_no": 5,            # 유저가 불가(B)이고 방이 비허용(False)
    "smoke": 10,
    "conv": 10,
    "time": 10,
    "noise": 6,
    "meal": 6,
    "weekend": 6,
    "space": 6,
}

def _eq_score(field_path: str, user_val, weight: int):
    # owner 또는 room의 필드와 유저 응답이 '정확히 일치'하면 가점
    if not user_val:
        return Value(0, output_field=IntegerField())
    return Case(
        When(**{field_path: user_val}, then=Value(weight)),
        default=Value(0),
        output_field=IntegerField(),
    )

def _recommend_queryset_for(user):
    qs = Room.objects.select_related("owner").all()

    # ── 지역 가점(관심지역과 일치할수록 높은 점수) ─────────────────────────
    score_region = Value(0, output_field=IntegerField())
    if getattr(user, "interested_province", None):
        score_region = score_region + Case(
            When(address_province=user.interested_province, then=Value(WEIGHTS["region_province"])),
            default=Value(0), output_field=IntegerField()
        )
    if getattr(user, "interested_city", None):
        score_region = score_region + Case(
            When(address_city=user.interested_city, then=Value(WEIGHTS["region_city"])),
            default=Value(0), output_field=IntegerField()
        )
    if getattr(user, "interested_district", None):
        score_region = score_region + Case(
            When(address_district=user.interested_district, then=Value(WEIGHTS["region_district"])),
            default=Value(0), output_field=IntegerField()
        )

    # ── 반려동물 ─────────────────────────────────────────────────────────
    # 유저 A(가능) → 방 pet_allowed=True 가점 / 유저 B(불가) → pet_allowed=False 가점
    if getattr(user, "pet_preference", None) == "A":
        score_pet = Case(
            When(pet_allowed=True, then=Value(WEIGHTS["pet_yes"])),
            default=Value(0), output_field=IntegerField()
        )
    elif getattr(user, "pet_preference", None) == "B":
        score_pet = Case(
            When(Q(pet_allowed=False) | Q(pet_allowed__isnull=True), then=Value(WEIGHTS["pet_no"])),
            default=Value(0), output_field=IntegerField()
        )
    else:
        score_pet = Value(0, output_field=IntegerField())

    # ── 시니어(집주인) 설문과의 매칭 ────────────────────────────────────────
    # 흡연/대화/시간/소음/식사/주말/공간공유는 owner의 응답과 유저 응답이 같으면 가점
    score_smoke  = _eq_score("owner__smoking_preference",      getattr(user, "smoking_preference", None),      WEIGHTS["smoke"])
    score_conv   = _eq_score("owner__conversation_style",      getattr(user, "conversation_style", None),      WEIGHTS["conv"])
    score_time   = _eq_score("owner__preferred_time",          getattr(user, "preferred_time", None),          WEIGHTS["time"])
    score_noise  = _eq_score("owner__noise_level",             getattr(user, "noise_level", None),             WEIGHTS["noise"])
    score_meal   = _eq_score("owner__meal_preference",         getattr(user, "meal_preference", None),         WEIGHTS["meal"])
    score_weekend= _eq_score("owner__weekend_preference",      getattr(user, "weekend_preference", None),      WEIGHTS["weekend"])
    score_space  = _eq_score("owner__space_sharing_preference",getattr(user, "space_sharing_preference", None),WEIGHTS["space"])

    # ── 합산 후 정렬 ───────────────────────────────────────────────────────
    qs = qs.annotate(
        score_region=score_region,
        score_pet=score_pet,
        score_smoke=score_smoke,
        score_conv=score_conv,
        score_time=score_time,
        score_noise=score_noise,
        score_meal=score_meal,
        score_weekend=score_weekend,
        score_space=score_space,
    ).annotate(
        match_score=(
            F("score_region") + F("score_pet") + F("score_smoke") + F("score_conv") +
            F("score_time") + F("score_noise") + F("score_meal") +
            F("score_weekend") + F("score_space")
        )
    ).order_by("-match_score", "-created_at")

    return qs

@require_GET
def autocomplete_region(request):
    query = request.GET.get("query", "").strip()
    if not query:
        return JsonResponse({"results": []}, json_dumps_params={'ensure_ascii': False})

    regions = Region.objects.filter(name__icontains=query).values_list("name", flat=True)[:10]
    return JsonResponse({"results": list(regions)}, json_dumps_params={'ensure_ascii': False})


@require_GET
def listings_by_region(request):
    region_name = request.GET.get("region", "").strip()
    if not region_name:
        return JsonResponse({"results": []}, json_dumps_params={'ensure_ascii': False})

    listings = Listing.objects.filter(region__name=region_name).values("title", "price", "description")
    return JsonResponse({"results": list(listings)}, json_dumps_params={'ensure_ascii': False})

# 홈 페이지를 캐시하지 않기
@never_cache
def home_view(request):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')
    if not getattr(request.user, "is_youth", False):
        return render(request, 'users/re_login.html')

    ids = request.session.get("recent_room_ids", [])
    recent_rooms = []
    if ids:
        preserved = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(ids)])
        recent_rooms = list(Room.objects.filter(id__in=ids).order_by(preserved))

    rooms = Room.objects.order_by("-created_at")[:8]
    categories = ["아파트", "빌라", "오피스텔", "주택"]

    resp = render(request, "home/home.html", {
        "rooms": rooms,
        "categories": categories,
        "recent_rooms": recent_rooms,
    })
    # 추가 방어 (일부 브라우저용)
    resp["Cache-Control"] = "no-store"
    return resp

