from django.shortcuts import render, get_object_or_404
from .models import Room
from matching.utils import calculate_matching_score

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

    # 설문조사 결과를 바탕으로 해시태그 리스트 생성
    hashtags = []
    # 활동 시간대
    if owner.preferred_time == 'A':
        hashtags.append('아침형')
    else:
        hashtags.append('저녁형')
    # 중요한 점
    if owner.important_points == 'A':
        hashtags.append('깔끔한')
    elif owner.important_points == 'B':
        hashtags.append('생활리듬')
    elif owner.important_points == 'C':
        hashtags.append('소통')
    elif owner.important_points == 'D':
        hashtags.append('배려심')
    else:
        hashtags.append('사생활존중')
    # 대화 스타일
    if owner.conversation_style == 'A':
        hashtags.append('조용함')
    else:
        hashtags.append('활발함')

    # 매칭 점수 계산
    matching_score = None
    # 로그인한 사용자가 청년(is_youth=True)인지 확인
    if request.user.is_authenticated and request.user.is_youth:
        # 매칭 점수 계산 함수 호출
        matching_score = calculate_matching_score(request.user, owner)

    context = {
        'room': room,
        'hashtags': hashtags,
        'matching_score': matching_score,
    }
    return render(request, 'room/room_detail.html', context)

def room_detail_test(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'room/room_detail.html', {'room': room})