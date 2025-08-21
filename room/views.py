from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room
from users.models import User
from matching.utils import calculate_matching_score, WEIGHTS
from django.contrib.auth.decorators import login_required
from matching.models import MoveInRequest
from django.urls import reverse

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

    matching_score = None
    is_requested_before = False

    # 로그인한 사용자가 청년(is_youth=True)인지 확인
    if request.user.is_authenticated and request.user.is_youth:
        matching_score = calculate_matching_score(request.user, owner)
        is_requested_before = MoveInRequest.objects.filter(youth=request.user, room=room).exists()

    context = {
        'room': room,
        'matching_score': matching_score,
        'is_requested_before': is_requested_before,
    }
    return render(request, 'room/room_detail.html', context)


@login_required
def senior_request_inbox(request):
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User is youth: {request.user.is_youth}")

    if not request.user.is_authenticated or request.user.is_youth:
        print(request.user.is_youth)
        print("로그인된 사용자가 청년 유형이므로 청년 홈으로 이동")
        return redirect(reverse('users:home_youth'))



    try:
        print("로그인된 사용자가 시니어 유형이므로 시니어 전용 '입주 희망 요청 보기' 로 이동")
        senior_rooms = Room.objects.filter(owner=request.user)
        requests = MoveInRequest.objects.filter(room__in=senior_rooms).order_by('-requested_at')

        context = {
            'requests': requests,
        }
        return render(request, 'room/senior_request_inbox.html', context)
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return HttpResponse(f"디버깅 중 오류 발생: {e}", status=500)

    # print("로그인된 사용자가 시니어 유형이므로 시니어 전용 '입주 희망 요청 보기' 로 이동")
    #
    # senior_rooms = Room.objects.filter(owner=request.user)
    # requests = MoveInRequest.objects.filter(roomin=senior_rooms).order_by('-requested_at')
    #
    # context = {
    #     'requests': requests,
    # }

    return render(request, 'room/senior_request_inbox.html', context)