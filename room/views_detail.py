# room/views_detail.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Avg, Count
from .models import Room
from users.views import get_matching_details
from review.models import Review

def _push_recent_room(session, room_id, limit=10):
    ids = session.get("recent_room_ids", [])
    ids = [i for i in ids if i != room_id]
    ids.insert(0, room_id)
    session["recent_room_ids"] = ids[:limit]
    session.modified = True

def room_detail(request, room_id):
    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')
    if not getattr(request.user, "is_youth", False):
        return render(request, 'users/re_login.html')

    room = get_object_or_404(
        Room.objects.prefetch_related('room_reviews'),  # related_name이 다르면 수정
        id=room_id
    )
    _push_recent_room(request.session, room.id)

    owner = getattr(room, "owner", None) or getattr(room, "host", None)

    # 매칭 계산
    matching_score = None
    matching_text = None
    explanation = None
    hashtags = []
    matching_percent = 0

    if request.user.is_authenticated and getattr(request.user, "is_youth", True) and owner:
        md = get_matching_details(request.user, owner)
        matching_score = md.get("matching_score")
        matching_text  = md.get("matching_text")
        explanation    = md.get("explanation")
        hashtags       = md.get("hashtags", [])
        try:
            matching_percent = int(round(float(matching_score or 0)))
        except (TypeError, ValueError):
            matching_percent = 0
        matching_percent = max(0, min(100, matching_percent))

    # ---------- 후기 데이터 ----------
    rv_qs = Review.objects.filter(room=room).order_by('-created_at')

    # 1) 개수/상단 3개
    rv_cnt = rv_qs.count()
    rv_top3 = list(rv_qs[:3])

    # 2) 문자열 만족도를 점수(1~5)로 매핑해 평균 구하기
    SAT_MAP = {
        'VERY_DISSATISFIED': 1,
        'DISSATISFIED': 2,
        'NORMAL': 3,
        'SATISFIED': 4,
        'VERY_SATISFIED': 5,
    }
    scores = [SAT_MAP.get(r.satisfaction, 0) for r in rv_qs]
    rv_avg = round(sum(scores) / len(scores), 1) if scores else 0.0

    # 3) 칩(간단 추출): 쉼표/줄바꿈 기준으로 분리 후 상위 몇 개만
    def _split_tags(text):
        if not text:
            return []
        parts = []
        for sep in [',', '\n', '·', ';', '/']:
            text = text.replace(sep, ',')
        for p in text.split(','):
            t = p.strip()
            if t:
                parts.append(t)
        return parts

    good_tags, bad_tags = [], []
    for r in rv_qs:
        good_tags.extend(_split_tags(r.good_points))
        bad_tags.extend(_split_tags(r.bad_points))

    # 중복 제거 + 앞쪽 몇 개만 노출
    def _dedup_keep_order(seq):
        seen, out = set(), []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
    rv_good_tags = _dedup_keep_order(good_tags)[:5]
    rv_bad_tags  = _dedup_keep_order(bad_tags)[:5]

    ctx = {
        "room": room,
        "owner": getattr(room, "owner", None),

        # 매칭
        "matching_score": matching_score,
        "matching_text": matching_text,
        "explanation": explanation,
        "hashtags": hashtags,
        "matching_percent": matching_percent,

        # 후기
        "rv_cnt": rv_cnt,
        "rv_avg": rv_avg,
        "rv_top3": rv_top3,
        "rv_good_tags": rv_good_tags,   # 예: ['깔끔해요', '햇볕이 잘 들어요']
        "rv_bad_tags": rv_bad_tags,     # 예: ['더워요', '세탁기 시간이 불규칙해요']
    }
    return render(request, "room/room_detail.html", ctx)

def room_detail_test(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return JsonResponse({"id": room.id, "name": getattr(room, "name", f"room-{room.id}")})
