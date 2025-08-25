from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Room

def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    ctx = {"room": room, "matching_score": None, "is_requested_before": False}
    return render(request, "room/room_detail.html", ctx)

def room_detail_test(request, room_id):
    # 테스트용, 단순히 JSON으로 반환할 수도 있음
    room = get_object_or_404(Room, id=room_id)
    return JsonResponse({"id": room.id, "name": room.name})

# 상세 페이지에 접속할 때 최근본 방 ID를 세션에 기록
def _push_recent_room(session, room_id, limit=10):
    ids = session.get("recent_room_ids", [])
    # 중복 제거 후 맨 앞에 추가
    ids = [i for i in ids if i != room_id]
    ids.insert(0, room_id)
    session["recent_room_ids"] = ids[:limit]
    session.modified = True

def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # ✅ 최근 본 방 세션 업데이트
    _push_recent_room(request.session, room.id)

    ctx = {"room": room, "matching_score": None, "is_requested_before": False}
    return render(request, "room/room_detail.html", ctx)

def room_detail_test(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return JsonResponse({"id": room.id, "name": getattr(room, "name", f"room-{room.id}")})
