from django.shortcuts import render, get_object_or_404
from .models import Room
from users.models import User
from matching.utils import calculate_matching_score, WEIGHTS

def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    owner = room.owner

    # --- 디버그 코드 추가 시작 ---
    print("--- 로그인 상태 디버그 ---")
    if request.user.is_authenticated:
        print(f"로그인 상태: 로그인 됨 (유저명: {request.user.username})")
        print(f"청년 유저 여부: {request.user.is_youth}")
    else:
        print("로그인 상태: 로그인 안 됨")
    print("-------------------------")

    # 매칭 점수 계산
    matching_score = None
    # 로그인한 사용자가 청년(is_youth=True)인지 확인
    if request.user.is_authenticated and request.user.is_youth:
        # 매칭 점수 계산 함수 호출
        matching_score = calculate_matching_score(request.user, owner)

    context = {
        'room': room,
        'matching_score': matching_score,
    }
    return render(request, 'room/room_detail.html', context)