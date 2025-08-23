from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room
from users.models import User
from matching.utils import calculate_matching_score, WEIGHTS
from django.contrib.auth.decorators import login_required
from matching.models import MoveInRequest
from django.urls import reverse
from review.models import Review
from django.db import models
from django.db.models import Avg, Case, When

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

    reviews = Review.objects.filter(room=room).order_by('-created_at')
    review_count = reviews.count()

    # 만족도 별점 평균 계산
    reviews_with_scores = reviews.annotate(
        satisfaction_score=Case(
            When(satisfaction='VERY_DISSATISFIED', then=1),
            When(satisfaction='DISSATISFIED', then=2),
            When(satisfaction='NORMAL', then=3),
            When(satisfaction='SATISFIED', then=4),
            When(satisfaction='VERY_SATISFIED', then=5),
            default=0,
            output_field=models.IntegerField()
        )
    )
    average_rating = reviews_with_scores.aggregate(Avg('satisfaction_score'))['satisfaction_score__avg']

    if average_rating is None:
        average_rating = 0.0

    ai_summary = "아직 등록된 후기가 없거나, AI 요약 생성에 필요한 데이터가 부족합니다."
    good_hashtags = []
    bad_hashtags = []

    context = {
        'room': room,
        'matching_score': matching_score,
        'is_requested_before': is_requested_before,
        'reviews': reviews,
        'review_count': review_count,
        'average_rating': average_rating,
        'ai_summary': ai_summary,
        'good_hashtags': good_hashtags,
        'bad_hashtags': bad_hashtags,
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

    print("로그인된 사용자가 시니어 유형이므로 시니어 전용 '입주 희망 요청 보기' 로 이동")
    
    senior_rooms = Room.objects.filter(owner=request.user)
    requests = MoveInRequest.objects.filter(roomin=senior_rooms).order_by('-requested_at')
    
    context = {
        'requests': requests,
    }
    return render(request, 'room/senior_request_inbox.html', context)

def all_reviews_for_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    reviews = Review.objects.filter(room=room).order_by('-created_at')

    context = {
        'room': room,
        'reviews': reviews,
    }
    return render(request, 'room/all_reviews_for_room.html', context)
