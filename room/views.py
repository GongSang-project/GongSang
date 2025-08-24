import json
import os
import google.generativeai as genai

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Room
from users.models import User
from matching.utils import calculate_matching_score, WEIGHTS
from matching.models import MoveInRequest
from django.urls import reverse
from review.models import Review
from django.db import models
from django.db.models import Avg, Case, When

genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')


def room_detail(request, room_id):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')

    if not request.user.is_youth:
        return render(request, 'users/re_login.html')

    room = get_object_or_404(Room, id=room_id)
    owner = room.owner

    matching_score = None
    is_requested_before = False
    ai_recommendation_reason = None

    # 로그인한 사용자가 청년(is_youth=True)인지 확인
    if request.user.is_authenticated and request.user.is_youth:
        matching_score = calculate_matching_score(request.user, owner)
        is_requested_before = MoveInRequest.objects.filter(youth=request.user, room=room).exists()

        ai_recommendations = request.session.get('ai_recommendations', {})
        ai_recommendation_reason = ai_recommendations.get(str(room.id))

    reviews = Review.objects.filter(room=room).order_by('-created_at')
    review_count = reviews.count()

    review_texts = " ".join([review.text for review in reviews if review.text])

    ai_summary = "아직 등록된 후기가 없거나, AI 요약 생성에 필요한 데이터가 부족합니다."
    good_hashtags = []
    bad_hashtags = []

    if review_texts:
        prompt = f"""
                아래 후기 텍스트들을 분석하여 전체 내용을 100자 이내로 간결하게 요약해줘.
                그리고 후기에서 긍정적인 내용과 부정적인 내용을 각각 3개의 해시태그로 추출해줘.

                <후기 텍스트>
                "{review_texts}"

                응답은 다음 JSON 형식으로만 제공해줘. 해시태그는 한글로.
                ```json
                {{
                    "summary": "<간결한 요약>",
                    "good_hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"],
                    "bad_hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"]
                }}
                ```
            """
        try:
            response = model.generate_content(prompt)
            # ... 응답 처리 로직
            # ai_summary, good_hashtags, bad_hashtags 변수 업데이트
        except Exception as e:
            print(f"Gemini API 호출 중 오류 발생: {e}")

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
        'ai_recommendation_reason': ai_recommendation_reason,
    }
    return render(request, 'room/room_detail.html', context)


def senior_request_inbox(request):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')

    if request.user.is_youth:
        return render(request, 'users/re_login.html')

    senior_rooms = Room.objects.filter(owner=request.user)
    requests = MoveInRequest.objects.filter(room__in=senior_rooms).order_by('-requested_at')

    context = {
        'requests': requests,
    }
    return render(request, 'room/senior_request_inbox.html', context)


def all_reviews_for_room(request, room_id):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')

    if not request.user.is_youth:
        return render(request, 'users/re_login.html')

    room = get_object_or_404(Room, id=room_id)
    reviews = Review.objects.filter(room=room).order_by('-created_at')

    context = {
        'room': room,
        'reviews': reviews,
    }
    return render(request, 'room/all_reviews_for_room.html', context)
