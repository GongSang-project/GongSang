# room/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import Room
from matching.models import MoveInRequest
from matching.utils import calculate_matching_score, get_matching_details

def room_detail(request, room_id):
    # owner(User)까지 한 번에 로드
    room = get_object_or_404(
        Room.objects.select_related("owner"),
        id=room_id
    )
    owner = room.owner

    # --- 디버그 로그 ---
    print("--- 로그인 상태 디버그 ---")
    if request.user.is_authenticated:
        print(f"로그인 상태: 로그인 됨 (유저명: {request.user.username})")
        print(f"청년 유저 여부: {getattr(request.user, 'is_youth', False)}")
    else:
        print("로그인 상태: 로그인 안 됨")
    print("-------------------------")

    # 기본 컨텍스트
    matching_score = None
    matching_text = None
    matching_explanation = None
    matching_hashtags = []
    is_requested_before = False

    # 로그인 + 청년만 매칭 계산
    if request.user.is_authenticated and getattr(request.user, "is_youth", False):
        youth_user = request.user

        # 점수/문구/해시태그 한 번에
        try:
            details = get_matching_details(youth_user, owner)
            matching_score = details.get("matching_score")
            matching_text = details.get("matching_text")
            matching_explanation = details.get("explanation")
            matching_hashtags = details.get("hashtags", [])
        except Exception as e:
            # utils 내부 오류가 나도 상세페이지는 떠야 하므로 안전하게 처리
            print(f"[matching] get_matching_details 오류: {e}")

        # 이전에 요청했는지
        is_requested_before = MoveInRequest.objects.filter(
            youth=youth_user, room=room
        ).exists()

    context = {
        "room": room,
        "matching_score": matching_score,               # int or None (예: 93)
        "matching_text": matching_text,                 # 예: "매우 잘 맞음 👍"
        "matching_explanation": matching_explanation,   # 예: "'생활리듬'과 '대화스타일'이 잘 맞아요."
        "matching_hashtags": matching_hashtags,         # 예: ["아침형","깔끔한","비흡연"]
        "is_requested_before": is_requested_before,
    }
    return render(request, "room/room_detail.html", context)


@login_required
def senior_request_inbox(request):
    # 시니어 전용 페이지
    if getattr(request.user, "is_youth", False):
        return redirect(reverse("users:home_youth"))

    # 내가 올린 방들에 대한 입주 요청함
    senior_rooms = Room.objects.filter(owner=request.user)
    requests = (
        MoveInRequest.objects
        .filter(room__in=senior_rooms)
        .select_related("room", "youth")   # N+1 방지 (요청자/방 정보 필요 시)
        .order_by("-requested_at")
    )

    context = {
        "requests": requests,
    }
    return render(request, "room/senior_request_inbox.html", context)
