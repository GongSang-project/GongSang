from django.db.models import Q
from .models import Room

def build_room_queryset(params):
    qs = Room.objects.select_related('owner').all()

    q = params.get('q')
    if q:
        qs = qs.filter(Q(address__icontains=q) | Q(nearest_subway__icontains=q))

    region = params.get('region')
    if region:
        qs = qs.filter(address__icontains=region)

    min_dep = params.get('min_deposit')
    if min_dep not in (None, ''):
        qs = qs.filter(deposit__gte=min_dep)

    max_dep = params.get('max_deposit')
    if max_dep not in (None, ''):
        qs = qs.filter(deposit__lte=max_dep)

    min_rent = params.get('min_rent')
    if min_rent not in (None, ''):
        qs = qs.filter(rent_fee__gte=min_rent)

    max_rent = params.get('max_rent')
    if max_rent not in (None, ''):
        qs = qs.filter(rent_fee__lte=max_rent)

    move_in_from = params.get('move_in_from')
    if move_in_from:
        qs = qs.filter(available_date__gte=move_in_from)

    short_term = params.get('short_term')
    if short_term in ('on', True, 'true', 'True', '1'):
        qs = qs.filter(can_short_term=True)

    # TODO: property_type / deal_type 필드 추가되면 여기에 조건 1~2줄만 더.
    return qs.order_by('-created_at')
