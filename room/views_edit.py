# room/views_edit.py
import os
from pathlib import Path
from datetime import date as dt_date
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone

from .models import Room
try:
    from .models import RoomExtra, RoomPhoto
except Exception:
    RoomExtra = None
    RoomPhoto = None

# 등록 플로우의 스텝 폼 재사용
from .forms import RoomStepAddressForm, RoomStepDetailForm, RoomStepContractForm

# ───── 세션 키 (등록과 충돌 안 나게 별도 키 사용)
EDIT_ROOM_ID      = "EDIT_ROOM_ID"           # 편집 대상 PK
EDIT_WIZARD_DATA  = "room_edit_wizard"       # 편집 스텝 데이터 dict
EDIT_PHOTOS_DATA  = "room_edit_photos"       # {'COMMON':[...], 'YOUTH':[...], 'BATHROOM':[...]}
EDIT_INTRO_TEXT   = "room_edit_intro"        # 소개 텍스트

def _senior_guard(request):
    return request.user.is_authenticated and not getattr(request.user, "is_youth", True)

def _wiz_get(request):
    return request.session.get(EDIT_WIZARD_DATA, {})

def _wiz_set(request, data):
    request.session[EDIT_WIZARD_DATA] = data
    request.session.modified = True

def _page_title():
    return "방 수정하기"

def _step_no(key: str) -> str:
    # 시안 기준: 01~05
    return {"address":"01", "contract":"02", "detail":"03", "facilities":"04", "photos":"05"}[key]

def _temp_save(upload, user_id) -> str:
    base = f"temp_edit/{user_id}/"
    rel  = base + upload.name
    Path(settings.MEDIA_ROOT, base).mkdir(parents=True, exist_ok=True)
    return default_storage.save(rel, upload)

def _clear_edit_session(request):
    for k in (EDIT_WIZARD_DATA, EDIT_PHOTOS_DATA, EDIT_INTRO_TEXT, EDIT_ROOM_ID):
        request.session.pop(k, None)
    request.session.modified = True

# ─────────────────────────────────────────────
# 0. 편집 시작
@login_required
@never_cache
def edit_start(request, room_id):
    if not _senior_guard(request):
        return redirect("users:home_youth")

    room = get_object_or_404(Room, pk=room_id, owner=request.user)

    # 이전 편집 세션 클리어 후 시작(예전 키 충돌 방지)
    _clear_edit_session(request)

    request.session[EDIT_ROOM_ID] = room.id
    _wiz_set(request, {
        "address": {
            "address_province": room.address_province or "",
            "address_city": room.address_city or "",
            "address_district": room.address_district or "",
            "address_detailed": room.address_detailed or "",
            "nearest_subway": room.nearest_subway or "",
        },
        "contract": {
            "deposit": room.deposit,
            "rent_fee": room.rent_fee,
            "utility_fee": room.utility_fee,
            "contract_type": "단기거주" if room.can_short_term else "월세",
            "can_short_term": room.can_short_term,
        },
        "detail": {
            # ✅ 새 구조
            "property_type": room.property_type,   # APARTMENT/VILLA/OFFICETEL/HOUSE 또는 None
            "room_count": getattr(room, "room_count", None),
            "toilet_count": room.toilet_count,
            "area": room.area,
        },
        "facilities": {
            "options": room.options or [],
            "security_facilities": room.security_facilities or [],
            "other_facilities": room.other_facilities or [],
            "parking_available": room.parking_available,
            "pet_allowed": room.pet_allowed,
            "heating_type": room.heating_type or None,
        },
    })
    request.session[EDIT_PHOTOS_DATA] = {"COMMON": [], "YOUTH": [], "BATHROOM": []}
    request.session[EDIT_INTRO_TEXT]  = getattr(getattr(room, "extra", None), "description", "") or ""
    request.session.modified = True

    return redirect("room:edit_step_address")

# ─────────────────────────────────────────────
# 1. 주소
@login_required
def edit_step_address(request):
    if not _senior_guard(request): return redirect("users:home_youth")
    if not request.session.get(EDIT_ROOM_ID): return redirect("room:owner_room_list")

    initial = _wiz_get(request).get("address", {})
    if request.method == "POST":
        form = RoomStepAddressForm(request.POST)
        if form.is_valid():
            wiz = _wiz_get(request)
            wiz["address"] = form.cleaned_data
            _wiz_set(request, wiz)
            return redirect("room:edit_step_contract")
    else:
        form = RoomStepAddressForm(initial=initial)

    return render(request, "room/edit/step_address.html", {
        "form": form,
        "step": _step_no("address"),
        "page_title": _page_title(),
    })

# 2. 거래
@login_required
def edit_step_contract(request):
    if not _senior_guard(request): return redirect("users:home_youth")
    if not request.session.get(EDIT_ROOM_ID): return redirect("room:owner_room_list")

    initial = _wiz_get(request).get("contract", {})
    initial_contract_type = initial.get("contract_type") or ("단기거주" if initial.get("can_short_term") else "월세")

    if request.method == "POST":
        form = RoomStepContractForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            chosen = request.POST.get("contract_type", initial_contract_type)
            data["contract_type"] = chosen
            data["can_short_term"] = (chosen == "단기거주")

            wiz = _wiz_get(request)
            wiz["contract"] = data
            _wiz_set(request, wiz)
            return redirect("room:edit_step_detail")
    else:
        form = RoomStepContractForm(initial=initial)

    return render(request, "room/edit/step_contract.html", {
        "form": form,
        "step": _step_no("contract"),
        "initial_contract_type": initial_contract_type,
        "page_title": _page_title(),
    })

# 3. 상세
@login_required
def edit_step_detail(request):
    if not _senior_guard(request): return redirect("users:home_youth")
    if not request.session.get(EDIT_ROOM_ID): return redirect("room:owner_room_list")

    initial = _wiz_get(request).get("detail", {})
    initial_intro = request.session.get(EDIT_INTRO_TEXT, "")

    if request.method == "POST":
        form = RoomStepDetailForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()  # property_type, room_count, toilet_count, area
            intro = (request.POST.get("intro") or "").strip()
            wiz = _wiz_get(request)
            wiz["detail"] = data
            _wiz_set(request, wiz)
            request.session[EDIT_INTRO_TEXT] = intro
            request.session.modified = True
            return redirect("room:edit_step_facilities")
    else:
        form = RoomStepDetailForm(initial=initial)

    return render(request, "room/edit/step_detail.html", {
        "form": form,
        "step": _step_no("detail"),
        "initial_intro": initial_intro,
        "page_title": _page_title(),
    })

# 4. 시설
@login_required
def edit_step_facilities(request):
    if not _senior_guard(request): return redirect("users:home_youth")
    if not request.session.get(EDIT_ROOM_ID): return redirect("room:owner_room_list")

    wiz   = _wiz_get(request)
    fac   = wiz.get("facilities", {})
    if request.method == "POST":
        options  = request.POST.getlist("options")
        security = request.POST.getlist("security_facilities")
        other    = request.POST.getlist("other_facilities")
        parking  = (request.POST.get("parking_available") == "true")
        pet      = (request.POST.get("pet_allowed") == "true")
        heating  = request.POST.get("heating_type") or None

        wiz["facilities"] = {
            "options": options, "security_facilities": security, "other_facilities": other,
            "parking_available": parking, "pet_allowed": pet, "heating_type": heating,
        }
        _wiz_set(request, wiz)
        return redirect("room:edit_step_photos")

    return render(request, "room/edit/step_facilities.html", {
        "step": _step_no("facilities"),
        "initial": fac,
        "page_title": _page_title(),
    })

# 5. 사진(마지막 스텝에서 저장까지)
@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def edit_step_photos(request):
    if not _senior_guard(request): return redirect("users:home_youth")
    if not request.session.get(EDIT_ROOM_ID): return redirect("room:owner_room_list")

    photos = request.session.get(EDIT_PHOTOS_DATA, {"COMMON":[], "YOUTH":[], "BATHROOM":[]})

    if request.method == "POST":
        def save_many(field_name, bucket_key):
            for f in request.FILES.getlist(field_name):
                name = f.name.lower()
                if not name.endswith((".jpg",".jpeg",".png",".webp",".gif",".heic",".heif")):
                    continue
                rel = _temp_save(f, request.user.id)
                photos[bucket_key] = photos.get(bucket_key, []) + [rel]

        save_many("common_photos",   "COMMON")
        save_many("youth_photos",    "YOUTH")
        save_many("bathroom_photos", "BATHROOM")

        # 저장 & 나가기
        if "save_and_exit" in request.POST:
            request.session[EDIT_PHOTOS_DATA] = photos
            request.session.modified = True
            _apply_edit_and_persist(request)     # ← 실제 DB 반영
            return HttpResponseRedirect(reverse("room:owner_room_list") + "?page=1")

        # 업로드만 반영(계속 편집)
        request.session[EDIT_PHOTOS_DATA] = photos
        request.session.modified = True

    return render(request, "room/edit/step_photos.html", {
        "step": _step_no("photos"),
        "photos": photos,
        "page_title": _page_title(),
    })

# ─────────────────────────────────────────────
# DB 반영 공통 로직
def _apply_edit_and_persist(request):
    room = get_object_or_404(Room, pk=request.session.get(EDIT_ROOM_ID), owner=request.user)
    wiz  = _wiz_get(request)

    addr = wiz.get("address", {})
    con  = wiz.get("contract", {})
    det  = wiz.get("detail", {})
    fac  = wiz.get("facilities", {})
    intro = request.session.get(EDIT_INTRO_TEXT, "")

    # 날짜는 수정 플로우엔 별도 스텝이 없으므로 기존값 유지(없으면 오늘)
    available_date = room.available_date or timezone.localdate()

    # 필드 반영 (✅ floor 제거, 새 필드 반영)
    room.deposit = con.get("deposit")
    room.rent_fee = con.get("rent_fee")
    room.utility_fee = con.get("utility_fee") or 0

    room.property_type = det.get("property_type") or None
    room.room_count = det.get("room_count")
    room.area = det.get("area")
    room.toilet_count = det.get("toilet_count")

    room.available_date = available_date
    room.can_short_term = bool(con.get("can_short_term"))

    room.address_province = addr.get("address_province") or ""
    room.address_city = addr.get("address_city") or ""
    room.address_district = addr.get("address_district") or ""
    room.address_detailed = addr.get("address_detailed") or ""
    room.nearest_subway = addr.get("nearest_subway") or ""

    room.options = fac.get("options", [])
    room.security_facilities = fac.get("security_facilities", [])
    room.other_facilities = fac.get("other_facilities", [])
    room.parking_available = fac.get("parking_available", False)
    room.pet_allowed = fac.get("pet_allowed", False)
    room.heating_type = fac.get("heating_type") or None
    room.save()

    if RoomExtra is not None:
        try:
            extra, _ = RoomExtra.objects.get_or_create(room=room)
            extra.description = intro
            extra.save()
        except Exception:
            pass

    # 새 업로드 사진 저장(기존 사진은 그대로 유지)
    if RoomPhoto is not None:
        photos = request.session.get(EDIT_PHOTOS_DATA, {"COMMON":[], "YOUTH":[], "BATHROOM":[]})
        for cat, rels in photos.items():
            for relpath in rels:
                try:
                    with default_storage.open(relpath, "rb") as f:
                        p = RoomPhoto(room=room, category=cat)
                        p.image.save(os.path.basename(relpath), File(f), save=True)
                    default_storage.delete(relpath)
                except Exception:
                    pass

    _clear_edit_session(request)
