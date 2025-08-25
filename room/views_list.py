# room/views_list.py
from urllib.parse import urlencode
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Room
import re

# 카테고리 별 키워드(한글/영문/변형 포함)
PT_ALIASES = {
    "APT": {"아파트", "아파트형", "APT", "apartment", "Apartment"},
    "OFFICETEL": {"오피스텔", "officetel", "OFFICETEL"},
    "VILLA": {"빌라", "연립", "다세대", "VILLA"},
    "HOUSE": {"주택", "단독", "다가구", "단독주택", "연립주택", "HOUSE"},
}

# 텍스트 검색에 사용할 필드들
PT_TEXT_FIELDS = [
    "address_province",
    "address_city",
    "address_district",
    "address_detailed",
    "nearest_subway",
    "owner_living_status",
]

def _has_field(model, name: str) -> bool:
    return any(f.name == name for f in model._meta.get_fields())

# ── 지역 토큰 표준화 ─────────────────────────────────────────────
def _aliases(token: str):
    t = (token or "").strip()
    if not t:
        return []
    alts = {t}
    swaps = {
        "서울특별시": "서울시", "부산광역시": "부산", "대구광역시": "대구",
        "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
        "울산광역시": "울산", "세종특별자치시": "세종",
    }
    if t in swaps:
        alts.add(swaps[t])
    for suffix in ("특별자치시", "특별시", "광역시", "자치구", "시", "구", "군"):
        if t.endswith(suffix):
            alts.add(t[: -len(suffix)])
    alts |= {a.replace(" ", "") for a in list(alts)}
    return list(alts)

def _apply_region_tokens(qs, text: str):
    tokens = [t for t in (text or "").replace("+", " ").split() if t.strip()]
    for t in tokens:
        q_obj = Q()
        for a in _aliases(t):
            q_obj |= (
                Q(address_city__icontains=a) |
                Q(address_district__icontains=a) |
                Q(address_province__icontains=a) |
                Q(address_detailed__icontains=a) |
                Q(nearest_subway__icontains=a)
            )
        if not q_obj.children:
            q_obj = (
                Q(address_city__icontains=t) |
                Q(address_district__icontains=t) |
                Q(address_province__icontains=t) |
                Q(address_detailed__icontains=t) |
                Q(nearest_subway__icontains=t)
            )
        qs = qs.filter(q_obj)
    return qs

# ── 카테고리 필터 유틸 ─────────────────────────────────────────
def _normalize_pt_code(pt_raw: str):
    if not pt_raw:
        return None
    s = pt_raw.strip()
    s_upper = s.upper()
    if s_upper in PT_ALIASES:
        return s_upper
    for code, names in PT_ALIASES.items():
        lowered = {n.lower() for n in names}
        if s.lower() in lowered:
            return code
    return None

def _apply_category_filter(qs, pt_raw: str):
    """
    property_type 필드가 없을 때 텍스트 기반으로 카테고리 필터.
    매칭 0건이면 필터를 적용하지 않고 (qs 원본 반환, matched=False).
    """
    term = (pt_raw or "").strip()
    if not term:
        return qs, False

    code = _normalize_pt_code(term)
    aliases = set(PT_ALIASES.get(code, {term})) if code else {term}

    cond = Q()
    for kw in aliases:
        if not kw:
            continue
        for field in PT_TEXT_FIELDS:
            if _has_field(Room, field):
                cond |= Q(**{f"{field}__icontains": kw})

    qs_try = qs.filter(cond).distinct()

    # 그래도 0건이면 상세주소 정규식으로 한 번 더
    if not qs_try.exists() and _has_field(Room, "address_detailed"):
        pattern = "|".join(re.escape(kw) for kw in aliases if kw)
        qs_try = qs.filter(address_detailed__iregex=pattern).distinct()

    if qs_try.exists():
        return qs_try, True
    # 백오프: 0건이면 필터 미적용
    return qs, False

# ───────────────────────────────────────────────────────────────

def room_list_page(request):
    qs = Room.objects.all().order_by('-created_at')

    # --- 공통 검색 ---
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = _apply_region_tokens(qs, q)

    region = (request.GET.get('region') or '').strip()
    if region:
        qs = _apply_region_tokens(qs, region)

    # --- 카테고리 ---
    pt_raw = (request.GET.get('property_type') or '').strip()
    pt_no_hit = False
    if pt_raw:
        if _has_field(Room, 'property_type'):
            code = _normalize_pt_code(pt_raw)
            if code:
                before = qs.count()
                qs = qs.filter(property_type=code)
                if qs.count() == 0:
                    pt_no_hit = True
                    # 백오프: 코드로 0건이면 부분일치도 시도
                    qs = Room.objects.all().order_by('-created_at').filter(property_type__icontains=pt_raw)
            else:
                before = qs.count()
                qs = qs.filter(property_type__icontains=pt_raw)
                if qs.count() == 0:
                    pt_no_hit = True
                    qs = Room.objects.all().order_by('-created_at')
        else:
            qs, matched = _apply_category_filter(qs, pt_raw)
            pt_no_hit = not matched

    # --- 거래유형 & 가격 (필드 있을 때만) ---
    deal_type = (request.GET.get('deal_type') or '').strip().upper()
    if deal_type and _has_field(Room, 'deal_type'):
        qs = qs.filter(deal_type=deal_type)

    def _to_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    min_deposit_i = _to_int(request.GET.get('min_deposit'))
    max_deposit_i = _to_int(request.GET.get('max_deposit'))
    min_rent_i    = _to_int(request.GET.get('min_rent'))
    max_rent_i    = _to_int(request.GET.get('max_rent'))

    if min_deposit_i is not None:
        qs = qs.filter(deposit__gte=min_deposit_i)
    if max_deposit_i is not None:
        qs = qs.filter(deposit__lte=max_deposit_i)
    if min_rent_i is not None:
        qs = qs.filter(rent_fee__gte=min_rent_i)
    if max_rent_i is not None:
        qs = qs.filter(rent_fee__lte=max_rent_i)

    # --- 입주 가능일 ---
    move_in_from = (request.GET.get('move_in_from') or '').strip()
    if move_in_from:
        qs = qs.filter(available_date__gte=move_in_from)

    # --- 단기거주 ---
    if request.GET.get('short_term'):
        qs = qs.filter(can_short_term=True)

    total = qs.count()

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    base_qd = request.GET.copy()
    base_qd.pop('page', None)
    base_qs = urlencode(base_qd, doseq=True)
    if base_qs:
        base_qs += '&'
    prev_qs = f"{base_qs}page={page_obj.previous_page_number()}" if page_obj.has_previous() else ""
    next_qs = f"{base_qs}page={page_obj.next_page_number()}" if page_obj.has_next() else ""

    ctx = {
        "page_obj": page_obj,
        "total": total,
        "request": request,
        "prev_qs": prev_qs,
        "next_qs": next_qs,
        "display_region": region or q or "전체 지역",
        "pt_no_hit": pt_no_hit,  # ← 0건이면 True (템플릿에서 안내문 띄우기)
    }
    # 콘솔 디버깅용(원하면 지워도 됨)
    print(f"[room_list] q='{q}' region='{region}' property_type='{pt_raw}' total={total} pt_no_hit={pt_no_hit}")
    return render(request, 'room/room_list.html', ctx)
