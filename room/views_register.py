import os
import csv
import json
from pathlib import Path
from datetime import date as dt_date
from django.utils import timezone

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

from .forms import (
    DeedUploadRawForm,
    RoomStepAddressForm, RoomStepDetailForm, RoomStepContractForm, RoomStepPeriodForm
)
from .models import (
    Room,
    OPTION_CHOICES, SECURITY_CHOICES, OTHER_FACILITY_CHOICES, HEATING_CHOICES
)

# 선택적 import (존재하지 않을 수도 있는 부가 모델)
from django.apps import apps

try:
    RoomPhoto = apps.get_model('room', 'RoomPhoto')
except LookupError:
    RoomPhoto = None

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from django.conf import settings

from users.utils import decrypt_image

from django.http import HttpResponse
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

try:
    RoomExtra = apps.get_model('room', 'RoomExtra')
except LookupError:
    RoomExtra = None


# ─────────────────────────────────────────────────────────────
# 세션 키
DEED_TEMP_PATH = "deed_temp_path"      # temp 파일 상대경로
DEED_SOURCE    = "deed_source"         # 'camera' | 'file'
DEED_CONFIRMED = "deed_confirmed"      # True/False
WIZARD_DATA    = "room_wizard"         # 스텝 데이터 dict
PHOTOS_DATA    = "room_photos"         # {'COMMON':[...], 'YOUTH':[...], 'BATHROOM':[...]}
INTRO_TEXT     = "room_intro"
EDIT_ROOM_ID   = "EDIT_ROOM_ID"        # 수정 대상 Room.id (없으면 신규 등록)
DEED_TEMP_ENCRYPTED_DATA = "deed_temp_encrypted_data"

# ─────────────────────────────────────────────────────────────
# 공용 유틸

def encrypt_file_data(file):
    try:
        padded_data = pad(file.read(), AES.block_size)

        cipher = AES.new(settings.ENCRYPTION_KEY, AES.MODE_CBC)
        encrypted_data = cipher.encrypt(padded_data)

        return base64.b64encode(cipher.iv + encrypted_data).decode('utf-8')
    except Exception as e:
        print(f"암호화 오류: {e}")
        return None

def _senior_guard(request):
    return request.user.is_authenticated and not getattr(request.user, "is_youth", True)

def _is_edit_mode(request) -> bool:
    return bool(request.session.get(EDIT_ROOM_ID))

def _clear_deed_session(request):
    for k in (DEED_TEMP_ENCRYPTED_DATA, DEED_SOURCE, DEED_CONFIRMED):
        request.session.pop(k, None)
    request.session.modified = True

def _temp_save(upload, user_id) -> str:
    """임시 저장 후 상대경로 반환. (MEDIA_ROOT 기준)"""
    base = f"temp_deeds/{user_id}/"
    rel  = base + upload.name
    root = Path(settings.MEDIA_ROOT) / base
    root.mkdir(parents=True, exist_ok=True)
    # 동일파일명 충돌 방지
    name = default_storage.save(rel, upload)
    return name  # 예: 'temp_deeds/12/xxx.jpg'

def _is_image(path: str) -> bool:
    # HEIC/HEIF 포함 (iOS 카메라)
    return path.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"))

def _require_deed_confirmed(request):
    if _is_edit_mode(request):
        return True

    return request.session.get(DEED_CONFIRMED) is True and request.session.get(DEED_TEMP_ENCRYPTED_DATA)

def _wiz_get(request):
    return request.session.get(WIZARD_DATA, {})

def _wiz_set(request, data):
    request.session[WIZARD_DATA] = data
    request.session.modified = True


# ─────────────────────────────────────────────────────────────
# 주소 CSV → 트리(JSON) 로더 (API 없이 템플릿에서 바로 사용)
# 구조: { "시도": { "시군구": ["동/읍/면", ...] } }

_ADDR_TREE_CACHE = None
_ADDR_ERROR_MSG = None

def _addr_csv_path() -> Path:
    # 1) ENV
    p_env = os.environ.get("LEGALADDR_CSV_PATH")
    if p_env:
        p = Path(p_env)
        if p.exists():
            return p

    # 2) settings
    p_set = getattr(settings, "LEGALADDR_CSV_PATH", None)
    if p_set:
        p = Path(p_set)
        if p.exists():
            return p

    # 3) 고정 파일명 후보
    base = Path(settings.BASE_DIR) / "data"
    for name in ("regions.csv", "region.csv", "legaladdr.csv"):
        candidate = base / name
        if candidate.exists():
            return candidate

    # 4) 패턴 탐색
    for pat in ("region*.csv", "*법정*.csv", "*address*.csv"):
        for p in base.glob(pat):
            if p.is_file():
                return p

    # 최종 폴백(로그 안내용 경로)
    return base / "regions.csv"

def _open_csv_try_all_encodings(path: Path):
    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                text = f.read()
            return text, enc, None
        except FileNotFoundError:
            return None, None, f"CSV NOT FOUND: {path}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue
    return None, None, f"CSV OPEN FAILED for {path} (encodings tried: {', '.join(encodings)}). last={last_err}"

def _sniff_dialect(sample: str):
    import csv as _csv
    try:
        sniff = _csv.Sniffer()
        dialect = sniff.sniff(sample, delimiters=",\t;|")
        has_header = sniff.has_header(sample)
        return dialect, has_header
    except Exception:
        class D: delimiter = ","
        return D, True

def _norm_header(name: str) -> str:
    if not name:
        return ""
    n = name.strip()
    return n.replace(" ", "").replace("_", "").replace("-", "")

def _load_addr_tree():
    global _ADDR_TREE_CACHE, _ADDR_ERROR_MSG
    _ADDR_ERROR_MSG = None

    if _ADDR_TREE_CACHE is not None:
        return _ADDR_TREE_CACHE

    csv_path = _addr_csv_path()
    print(f"[ADDR] Loading CSV: {csv_path}")

    text, used_enc, open_err = _open_csv_try_all_encodings(csv_path)
    if open_err:
        print(f"[ADDR] {open_err}")
        _ADDR_ERROR_MSG = open_err
        return {}

    # 구분자/헤더 감지
    dialect, has_header = _sniff_dialect(text[:8192])
    try:
        rows = []
        reader = csv.reader(text.splitlines(), delimiter=dialect.delimiter)
        for r in reader:
            rows.append(r)
    except Exception as e:
        _ADDR_ERROR_MSG = f"CSV PARSE ERROR: {type(e).__name__}: {e}"
        print(f"[ADDR] {_ADDR_ERROR_MSG}")
        return {}

    if not rows:
        _ADDR_ERROR_MSG = "CSV EMPTY"
        print(f"[ADDR] CSV EMPTY")
        return {}

    # 헤더 처리
    header_map = {}
    start_idx = 0
    if has_header:
        headers = rows[0]
        start_idx = 1
        norm_headers = [_norm_header(h) for h in headers]

        candidates = {
            "sido": {"시도명", "시도", "sido"},
            "sigungu": {"시군구명", "시군구", "구군", "sigungu", "si_gun_gu"},
            "dong": {"읍면동명", "읍면동", "행정동", "dong", "eupmyeondong"},
            "deleted": {"삭제일자", "삭제일", "deleted", "delete", "del"},
        }

        def find_idx(keys):
            for i, h in enumerate(norm_headers):
                for k in keys:
                    if _norm_header(k) == h:
                        return i
            return None

        idx_sido = find_idx(candidates["sido"])
        idx_sigungu = find_idx(candidates["sigungu"])
        idx_dong = find_idx(candidates["dong"])
        idx_del = find_idx(candidates["deleted"])

        header_map = {"sido": idx_sido, "sigungu": idx_sigungu, "dong": idx_dong, "deleted": idx_del}
    else:
        # 헤더 없음: 표준 열 순서 가정
        # 0:법정동코드, 1:시도명, 2:시군구명, 3:읍면동명, 4:리명, 5:순위, 6:생성일자, 7:삭제일자, 8:과거법정동코드
        header_map = {"sido": 1, "sigungu": 2, "dong": 3, "deleted": 7}

    if header_map["sido"] is None or header_map["dong"] is None:
        _ADDR_ERROR_MSG = "CSV HEADER MISMATCH: '시도명'/'읍면동명' 열을 찾을 수 없습니다. 헤더를 확인하세요."
        print(f"[ADDR] {_ADDR_ERROR_MSG}")
        return {}

    tree: dict[str, dict[str, list[str]]] = {}
    total = 0
    for r in rows[start_idx:]:
        try:
            s = (r[header_map["sido"]] or "").strip()
            g = (r[header_map["sigungu"]] or "").strip() if header_map["sigungu"] is not None else ""
            d = (r[header_map["dong"]] or "").strip()
            delv = (r[header_map["deleted"]] or "").strip() if header_map["deleted"] is not None else ""

            if delv:
                continue
            if not s:
                continue
            if not g and d:
                g = s  # 세종 등 시군구 공란 케이스

            tree.setdefault(s, {})
            if g:
                tree[s].setdefault(g, [])
            if g and d and d not in tree[s][g]:
                tree[s][g].append(d)
            total += 1
        except IndexError:
            continue

    # 정렬
    for s, gmap in tree.items():
        for g, dlist in gmap.items():
            gmap[g] = sorted(set(dlist))

    if not tree:
        if _ADDR_ERROR_MSG is None:
            _ADDR_ERROR_MSG = "CSV LOADED BUT NO ROWS MATCH FILTER"
        print(f"[ADDR] {_ADDR_ERROR_MSG}")
        return {}

    # 통계 로그
    try:
        sidos = len(tree)
        sigungus = sum(len(gmap) for gmap in tree.values())
        dongs = sum(len(dlist) for gmap in tree.values() for dlist in gmap.values())
        print(f"[ADDR] Loaded(enc={used_enc}, delim='{dialect.delimiter}', header={has_header}): "
              f"{sidos} sidos, {sigungus} sigungus, {dongs} dongs (rows read={total})")
    except Exception:
        pass

    _ADDR_TREE_CACHE = tree
    return tree

def _get_addr_error():
    return _ADDR_ERROR_MSG


# ─────────────────────────────────────────────────────────────
# 0. 등기부 업로드 시작 (카메라/파일 한 화면, 선택 즉시 업로드)

@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def deed_start(request):
    if not _senior_guard(request):
        return redirect("users:home_youth")

    # 수정 모드는 등기부 단계를 통째로 건너뜀
    if _is_edit_mode(request):
        return redirect("room:register_step_address")

    ctx = {"error": None}

    if request.method == "POST":
        form = DeedUploadRawForm(request.POST, request.FILES)
        source = request.POST.get("source") or "file"
        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]

            try:
                # 암호화된 데이터를 문자열로 인코딩하여 세션에 저장
                encrypted_data = encrypt_file_data(uploaded_file)
            except Exception:
                ctx["error"] = "파일 암호화 중 오류가 발생했습니다."
                return render(request, "room/register/deed_start.html", ctx)

            # 암호화된 데이터를 세션에 저장
            request.session[DEED_TEMP_ENCRYPTED_DATA] = encrypted_data
            request.session[DEED_SOURCE] = "camera" if source == "camera" else "file"
            request.session[DEED_CONFIRMED] = False
            request.session.modified = True

            return redirect("room:deed_preview")
        else:
            ctx["error"] = "; ".join([str(err) for errs in form.errors.values() for err in errs])
            return render(request, "room/register/deed_start.html", ctx)

    return render(request, "room/register/deed_start.html", ctx)


# 1. 미리보기 (다시 촬영/첨부, 확인)

@login_required
def deed_preview(request):
    if not _senior_guard(request):
        return redirect("users:home_youth")
    if _is_edit_mode(request):
        return redirect("room:register_step_address")

    encrypted_data = request.session.get(DEED_TEMP_ENCRYPTED_DATA)
    if not encrypted_data:
        return redirect("room:deed_start")

    from django.urls import reverse
    ctx = {
        "file_url": reverse('room:deed_preview_stream'),
        "source": request.session.get(DEED_SOURCE, "file"),

        "is_image": True
    }
    return render(request, "room/register/deed_preview.html", ctx)

@login_required
def deed_retry(request):
    if not _senior_guard(request):
        return redirect("users:home_youth")
    if _is_edit_mode(request):
        return redirect("room:register_step_address")

    _clear_deed_session(request)
    return redirect("room:deed_start")

@login_required
def deed_confirm(request):
    if not _senior_guard(request):
        return redirect("users:home_youth")
    if _is_edit_mode(request):
        return redirect("room:register_step_address")

    if not request.session.get(DEED_TEMP_ENCRYPTED_DATA):
        return redirect("room:deed_start")

    request.session[DEED_CONFIRMED] = True
    request.session.modified = True
    return redirect("room:register_step_address")


# ─────────────────────────────────────────────────────────────
# 2. 스텝들

@login_required
@never_cache
def register_step_address(request):
    if not _senior_guard(request):
        return redirect("users:home_youth")
    if not _require_deed_confirmed(request):
        return redirect("room:deed_start")

    addr_tree = _load_addr_tree()
    addr_tree_json = json.dumps(addr_tree, ensure_ascii=False)

    initial = _wiz_get(request).get("address", {})
    error = None

    if request.method == "POST":
        form = RoomStepAddressForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            s = data.get("address_province")
            g = data.get("address_city")
            d = data.get("address_district")
            ok = bool(s in addr_tree and g in addr_tree.get(s, {}) and d in addr_tree.get(s, {}).get(g, []))

            if not ok:
                error = "유효한 행정동을 선택해 주세요."
            else:
                wizard = _wiz_get(request)
                wizard["address"] = data
                _wiz_set(request, wizard)
                return redirect("room:register_step_detail")
    else:
        form = RoomStepAddressForm(initial=initial)

    csv_path_str = str(_addr_csv_path())
    addr_tree_empty = (len(addr_tree) == 0)
    addr_error = _get_addr_error()

    return render(
        request,
        "room/register/step_address.html",
        {
            "form": form,
            "step": "2/9",
            "addr_tree_json": addr_tree_json,
            "error": error,
            "addr_tree_empty": addr_tree_empty,
            "addr_csv_path": csv_path_str,
            "addr_error": addr_error,
        },
    )

@login_required
def register_step_detail(request):
    if not _senior_guard(request):
        return redirect("users:home_youth")
    if not _require_deed_confirmed(request):
        return redirect("room:deed_start")

    initial = _wiz_get(request).get("detail", {})

    if request.method == "POST":
        form = RoomStepDetailForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()  # {'property_type', 'room_count', 'toilet_count', 'area'}
            wizard = _wiz_get(request)
            wizard["detail"] = data
            _wiz_set(request, wizard)
            return redirect("room:register_step_contract")
    else:
        form = RoomStepDetailForm(initial=initial)

    return render(
        request,
        "room/register/step_detail.html",
        {
            "form": form,
            "step": "3/9",
        },
    )

@login_required
def register_step_contract(request):
    if not _senior_guard(request):
        return redirect("users:home_youth")
    if not _require_deed_confirmed(request):
        return redirect("room:deed_start")

    initial = _wiz_get(request).get("contract", {})
    contract_types = ["월세", "단기거주"]
    initial_contract_type = initial.get("contract_type") or ("단기거주" if initial.get("can_short_term") else "월세")

    if request.method == "POST":
        form = RoomStepContractForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            chosen = request.POST.get("contract_type", initial_contract_type)
            data["contract_type"] = chosen
            data["can_short_term"] = (chosen == "단기거주")

            wizard = _wiz_get(request)
            wizard["contract"] = data
            _wiz_set(request, wizard)
            return redirect("room:register_step_period")
    else:
        form = RoomStepContractForm(initial=initial)

    return render(
        request,
        "room/register/step_contract.html",
        {
            "form": form,
            "step": "4/9",
            "contract_types": contract_types,
            "initial_contract_type": initial_contract_type,
        },
    )

@login_required
def register_step_period(request):
    if not _senior_guard(request):
        return redirect("users:home_youth")
    if not _require_deed_confirmed(request):
        return redirect("room:deed_start")

    initial = _wiz_get(request).get("period", {})
    if request.method == "POST":
        form = RoomStepPeriodForm(request.POST)
        if form.is_valid():
            period = form.cleaned_data.copy()           # {'available_date': <date>}
            ad = period.get("available_date")
            if ad and hasattr(ad, "isoformat"):
                period["available_date"] = ad.isoformat()   # 세션 JSON 직렬화

            # (선택) UI 전용 값 보존
            period["stay_term"] = request.POST.get("stay_term", initial.get("stay_term", "1개월"))
            period["trial_ok"]  = request.POST.get("trial_ok",  initial.get("trial_ok", "예"))

            wiz = _wiz_get(request)
            wiz["period"] = period
            _wiz_set(request, wiz)

            return redirect("room:register_step_facilities")
    else:
        form = RoomStepPeriodForm(initial=initial)

    return render(request, "room/register/step_period.html", {
        "form": form, "step": "5/9",
        "stay_terms": ["1개월","3개월","6개월","1년 이상"],
        "initial_stay_term": initial.get("stay_term", "1개월"),
        "initial_trial_ok": initial.get("trial_ok", "예"),
    })

# 6/9 시설 통합(생활/보안/기타 + 주차/반려/난방) → 저장만
@login_required
def register_step_facilities(request):
    if not _senior_guard(request): return redirect("users:home_youth")
    if not _require_deed_confirmed(request): return redirect("room:deed_start")

    wiz = _wiz_get(request)
    fac1 = wiz.get("fac1", {})
    fac2 = wiz.get("fac2", {})

    initial_options  = fac1.get("options", [])
    initial_security = fac1.get("security_facilities", [])
    initial_other    = fac2.get("other_facilities", [])
    initial_parking  = fac2.get("parking_available", False)
    initial_pet      = fac2.get("pet_allowed", False)
    initial_heating  = fac2.get("heating_type", "")

    if request.method == "POST":
        options  = request.POST.getlist("options")
        security = request.POST.getlist("security_facilities")
        other    = request.POST.getlist("other_facilities")
        parking  = (request.POST.get("parking_available") == "true")
        pet      = (request.POST.get("pet_allowed") == "true")
        heating  = request.POST.get("heating_type") or None

        wiz["fac1"] = {"options": options, "security_facilities": security}
        wiz["fac2"] = {
            "other_facilities": other,
            "parking_available": parking,
            "pet_allowed": pet,
            "heating_type": heating,
        }
        _wiz_set(request, wiz)

        return redirect("room:register_step_photos")

    return render(request, "room/register/step_facilities.html", {
        "step": "6/9",
        "option_choices": OPTION_CHOICES,
        "security_choices": SECURITY_CHOICES,
        "other_choices": OTHER_FACILITY_CHOICES,
        "heating_choices": HEATING_CHOICES,
        "initial_options": initial_options,
        "initial_security": initial_security,
        "initial_other": initial_other,
        "initial_parking": initial_parking,
        "initial_pet": initial_pet,
        "initial_heating": initial_heating,
    })

# 8/9 사진 업로드 (카테고리별, 총 3~15장)
@login_required
@never_cache
def register_step_photos(request):
    if not _senior_guard(request): return redirect("users:home_youth")
    if not _require_deed_confirmed(request): return redirect("room:deed_start")

    photos = request.session.get(PHOTOS_DATA, {"COMMON":[], "YOUTH":[], "BATHROOM":[]})
    error = None
    edit_mode = _is_edit_mode(request)

    if request.method == "POST":
        # 테스트
        print("[PHOTOS:FILES:keys]", list(request.FILES.keys()))
        print("[PHOTOS:FILES:common]", len(request.FILES.getlist("common_photos")))
        print("[PHOTOS:FILES:youth]", len(request.FILES.getlist("youth_photos")))
        print("[PHOTOS:FILES:bath]", len(request.FILES.getlist("bathroom_photos")))
        def save_many(field_name, bucket_key):
            uploaded = request.FILES.getlist(field_name)
            if not uploaded:
                return
            rels = []
            for f in uploaded:
                if not f.name.lower().endswith((".jpg",".jpeg",".png",".webp",".gif",".heic",".heif")):
                    continue
                rels.append(_temp_save(f, request.user.id))
            photos[bucket_key] = photos.get(bucket_key, []) + rels

        save_many("common_photos",   "COMMON")
        save_many("youth_photos",    "YOUTH")
        save_many("bathroom_photos", "BATHROOM")

        # 테스트
        request.session[PHOTOS_DATA] = photos
        request.session.modified = True
        print("[PHOTOS:SESSION:AFTER]", request.session.get(PHOTOS_DATA))

        total = sum(len(v) for v in photos.values())
        if not edit_mode:  # 신규 등록만 최소/최대 검사
            if total < 3:
                error = "최소 3장 이상 업로드해주세요."
            elif total > 15:
                error = "최대 15장까지 업로드할 수 있어요."

        if error is None:
            request.session[PHOTOS_DATA] = photos
            request.session.modified = True
            return redirect("room:register_step_intro")

    return render(request, "room/register/step_photos.html", {
        "step": "8/9", "error": error, "photos": photos, "edit_mode": edit_mode
    })

# 9/9 집 소개 → 여기서 최종 생성/수정
@login_required
def register_step_intro(request):
    if not _senior_guard(request): return redirect("users:home_youth")
    if not _require_deed_confirmed(request): return redirect("room:deed_start")

    edit_mode = _is_edit_mode(request)

    if request.method == "POST":
        intro = (request.POST.get("intro") or "").strip()
        request.session[INTRO_TEXT] = intro
        request.session.modified = True

        wiz = _wiz_get(request)
        addr, det, con, per = wiz["address"], wiz["detail"], wiz["contract"], wiz["period"]

        # 테스트
        photos = request.session.get(PHOTOS_DATA, {})
        print("[INTRO:PHOTOS:SESSION]", request.session.get(PHOTOS_DATA))
        if RoomPhoto is None:
            print("[INTRO:SAVE] RoomPhoto is None → 모델 import 실패 또는 존재하지 않음")
        else:
            saved = 0
            photos = request.session.get(PHOTOS_DATA, {"COMMON": [], "YOUTH": [], "BATHROOM": []})
            for cat, rels in photos.items():
                for relpath in rels:
                    try:
                        print("[INTRO:SAVE:TRY]", cat, relpath)
                        with default_storage.open(relpath, "rb") as f:
                            p = RoomPhoto(room=room, category=cat)
                            p.image.save(os.path.basename(relpath), File(f), save=True)  # ★ save=True 필수
                        default_storage.delete(relpath)
                        saved += 1
                    except Exception as e:
                        print("[INTRO:SAVE:ERR]", type(e).__name__, e)
            print("[INTRO:SAVE:COUNT]", saved)


        # 날짜 복원
        ad = per.get("available_date")
        try:
            available_date = dt_date.fromisoformat(ad) if not isinstance(ad, dt_date) else ad
        except Exception:
            available_date = timezone.localdate()

        if edit_mode:
            # ─── UPDATE ───
            room = get_object_or_404(Room, pk=request.session[EDIT_ROOM_ID], owner=request.user)
            # 기본 정보 업데이트
            room.deposit = con["deposit"]
            room.rent_fee = con["rent_fee"]
            room.utility_fee = con.get("utility_fee") or 0
            room.area = det["area"]
            room.toilet_count = det["toilet_count"]
            room.property_type = det["property_type"]
            room.room_count = det["room_count"]
            room.available_date = available_date
            room.can_short_term = bool(con.get("can_short_term"))
            room.address_province = addr["address_province"]
            room.address_city = addr["address_city"]
            room.address_district = addr["address_district"]
            room.address_detailed = addr["address_detailed"]
            room.nearest_subway = addr.get("nearest_subway") or ""
            room.options = wiz.get("fac1", {}).get("options", [])
            room.security_facilities = wiz.get("fac1", {}).get("security_facilities", [])
            room.other_facilities = wiz.get("fac2", {}).get("other_facilities", [])
            room.parking_available = wiz.get("fac2", {}).get("parking_available", False)
            room.pet_allowed = wiz.get("fac2", {}).get("pet_allowed", False)
            room.heating_type = wiz.get("fac2", {}).get("heating_type") or None
            room.save()

            # 소개 저장/갱신
            if RoomExtra is not None:
                try:
                    extra, _ = RoomExtra.objects.get_or_create(room=room)
                    extra.description = intro
                    extra.save()
                except Exception:
                    pass

            # 새로 업로드된 사진만 추가
            if RoomPhoto is not None:
                photos = request.session.get(PHOTOS_DATA, {"COMMON":[], "YOUTH":[], "BATHROOM":[]})
                for cat, rels in photos.items():
                    for relpath in rels:
                        try:
                            with default_storage.open(relpath, "rb") as f:
                                p = RoomPhoto(room=room, category=cat)
                                p.image.save(os.path.basename(relpath), File(f), save=True)
                            default_storage.delete(relpath)
                        except Exception:
                            pass

            redirect_url = "room:owner_room_list"

        else:
            # ─── CREATE ───
            room = Room.objects.create(
                owner=request.user,
                deposit=con["deposit"],
                rent_fee=con["rent_fee"],
                utility_fee=con.get("utility_fee") or 0,
                area=det["area"],
                toilet_count=det["toilet_count"],
                property_type=det["property_type"],
                room_count=det["room_count"],
                available_date=available_date,
                can_short_term=bool(con.get("can_short_term")),
                address_province=addr["address_province"],
                address_city=addr["address_city"],
                address_district=addr["address_district"],
                address_detailed=addr["address_detailed"],
                nearest_subway=addr.get("nearest_subway") or "",
                options=wiz.get("fac1", {}).get("options", []),
                security_facilities=wiz.get("fac1", {}).get("security_facilities", []),
                other_facilities=wiz.get("fac2", {}).get("other_facilities", []),
                parking_available=wiz.get("fac2", {}).get("parking_available", False),
                pet_allowed=wiz.get("fac2", {}).get("pet_allowed", False),
                heating_type=wiz.get("fac2", {}).get("heating_type") or None,
            )

            # 암호화된 등기부등본 데이터 저장
            encrypted_data = request.session.get(DEED_TEMP_ENCRYPTED_DATA)
            if encrypted_data:
                room.land_register_document = encrypted_data
                room.is_land_register_verified = True
                room.save()

            # 소개 저장
            if RoomExtra is not None:
                try:
                    RoomExtra.objects.create(room=room, description=intro)
                except Exception:
                    pass

            # 사진 저장
            if RoomPhoto is not None:
                photos = request.session.get(PHOTOS_DATA, {"COMMON":[], "YOUTH":[], "BATHROOM":[]})
                for cat, rels in photos.items():
                    for relpath in rels:
                        try:
                            with default_storage.open(relpath, "rb") as f:
                                p = RoomPhoto(room=room, category=cat)
                                p.image.save(os.path.basename(relpath), File(f), save=True)
                            default_storage.delete(relpath)
                        except Exception:
                            pass

            redirect_url = "room:owner_room_list"

        # 세션 정리
        for k in (WIZARD_DATA, DEED_TEMP_PATH, DEED_SOURCE, DEED_CONFIRMED, PHOTOS_DATA, INTRO_TEXT, EDIT_ROOM_ID):
            request.session.pop(k, None)
        request.session.modified = True

        # 현재 플로우에선 상세 페이지로 안 보내고 내 방 목록으로 이동
        return redirect(redirect_url)

    # GET → 소개 입력 화면
    return render(request, "room/register/step_intro.html", {
        "step": "9/9",
        "edit_mode": edit_mode,
        "initial_intro": request.session.get(INTRO_TEXT, ""),
    })


def decrypt_file_data(encrypted_data_str):
    try:
        decoded_data = base64.b64decode(encrypted_data_str)
        iv = decoded_data[:AES.block_size]
        encrypted_data = decoded_data[AES.block_size:]

        cipher = AES.new(settings.ENCRYPTION_KEY, AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(encrypted_data)
        return unpad(decrypted_data, AES.block_size)
    except Exception as e:
        print(f"복호화 오류: {e}")
        return None


@login_required
def deed_preview_stream(request):
    if not _senior_guard(request):
        return HttpResponse("권한이 없습니다.", status=403)

    encrypted_data = request.session.get(DEED_TEMP_ENCRYPTED_DATA)
    if not encrypted_data:
        return HttpResponse("파일을 찾을 수 없습니다.", status=404)

    decrypted_data = decrypt_image(encrypted_data)  # users.utils의 함수 사용
    if not decrypted_data:
        return HttpResponse("파일을 불러올 수 없습니다.", status=500)


    content_type = 'application/pdf'

    return HttpResponse(decrypted_data, content_type=content_type)