# room/views.py
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from django.db import models
from django.db.models import Avg, Case, When

from .models import Room
from matching.models import MoveInRequest
from matching.utils import calculate_matching_score, get_matching_details
from review.models import Review


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

    # 리뷰/평점
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
    average_rating = reviews_with_scores.aggregate(
        Avg('satisfaction_score')
    )['satisfaction_score__avg'] or 0.0

    # TODO: 리뷰 요약/해시태그 로직 연동
    ai_summary = "아직 등록된 후기가 없거나, AI 요약 생성에 필요한 데이터가 부족합니다."
    good_hashtags = []
    bad_hashtags = []

    context = {
        "room": room,
        "matching_score": matching_score,               # int or None (예: 93)
        "matching_text": matching_text,                 # 예: "매우 잘 맞음 👍"
        "matching_explanation": matching_explanation,   # 예: "'생활리듬'과 '대화스타일'이 잘 맞아요."
        "matching_hashtags": matching_hashtags,         # 예: ["아침형","깔끔한","비흡연"]
        "is_requested_before": is_requested_before,

        # 리뷰 관련
        "reviews": reviews,
        "review_count": review_count,
        "average_rating": average_rating,
        "ai_summary": ai_summary,
        "good_hashtags": good_hashtags,
        "bad_hashtags": bad_hashtags,
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
        .select_related("room", "youth")   # 필요 시 N+1 방지
        .order_by("-requested_at")
    )

    context = {
        "requests": requests,
    }
    return render(request, "room/senior_request_inbox.html", context)


def all_reviews_for_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    reviews = Review.objects.filter(room=room).order_by('-created_at')

    context = {
        'room': room,
        'reviews': reviews,
    }
    return render(request, 'room/all_reviews_for_room.html', context)
