# room/views_list.py
from urllib.parse import urlencode
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Room


def _has_field(model, name: str) -> bool:
    return any(f.name == name for f in model._meta.get_fields())


# ── 여기 추가: 행정구역 토큰 표준화 ─────────────────────────────────────────────
def _aliases(token: str):
    """
    사용자가 '서울특별시 관악구'처럼 풀네임으로 입력해도
    DB가 '서울시/관악구' 또는 '서울/관악' 등으로 저장되어 있어 매칭되도록
    다양한 변형 후보를 만든다.
    """
    t = (token or "").strip()
    if not t:
        return []

    alts = {t}

    # 흔한 치환
    swaps = {
        "서울특별시": "서울시",
        "부산광역시": "부산",
        "대구광역시": "대구",
        "인천광역시": "인천",
        "광주광역시": "광주",
        "대전광역시": "대전",
        "울산광역시": "울산",
        "세종특별자치시": "세종",
    }
    if t in swaps:
        alts.add(swaps[t])

    # 접미사 제거 버전들
    for suffix in ("특별자치시", "특별시", "광역시", "자치구", "시", "구", "군"):
        if t.endswith(suffix):
            alts.add(t[: -len(suffix)])

    # 공백 제거 버전
    alts |= {a.replace(" ", "") for a in list(alts)}

    return list(alts)


def _apply_region_tokens(qs, text: str):
    """
    입력 문자열을 공백 기준 토큰으로 나눈 뒤,
    각 토큰에 대해 alias들을 만들어(서울특별시→서울시/서울 등)
    여러 주소 관련 필드(OR) 중 하나라도 매칭되면 통과.
    토큰들끼리는 AND로 누적 필터링.
    """
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
        # alias가 없으면 원 토큰으로라도 한 번 매칭 시도
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
# ────────────────────────────────────────────────────────────────────────────


def room_list_page(request):
    qs = Room.objects.all().order_by('-created_at')

    # --- 공통 검색 ---
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = _apply_region_tokens(qs, q)

    region = (request.GET.get('region') or '').strip()
    if region:
        qs = _apply_region_tokens(qs, region)

    # --- 매물유형 (모델에 있을 때만) ---
    property_type = (request.GET.get('property_type') or '').strip().upper()
    if property_type and _has_field(Room, 'property_type'):
        qs = qs.filter(property_type=property_type)

    # --- 거래유형 & 가격 (모델에 있을 때만) ---
    deal_type = (request.GET.get('deal_type') or '').strip().upper()
    if deal_type and _has_field(Room, 'deal_type'):
        qs = qs.filter(deal_type=deal_type)

    # 가격 파라미터
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
    move_in_from = request.GET.get('move_in_from')
    if move_in_from:
        qs = qs.filter(available_date__gte=move_in_from)

    # --- 단기거주 ---
    if request.GET.get('short_term'):
        qs = qs.filter(can_short_term=True)

    total = qs.count()

    # --- 페이징 ---
    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    # --- 페이지 쿼리스트링 ---
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
    }
    return render(request, 'room/room_list.html', ctx)
