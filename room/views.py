import json
import os
import google.generativeai as genai

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from django.db import models
from django.db.models import Avg, Case, When

from .models import Room
from review.models import Review
from matching.models import MoveInRequest
from matching.utils import calculate_matching_score, get_matching_details

genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')



def room_detail(request, room_id):
    # 비로그인 또는 청년 아님 → 로그인 유도
    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')
    if not getattr(request.user, "is_youth", False):
        return render(request, 'users/re_login.html')

    room = get_object_or_404(Room, id=room_id)
    owner = room.owner

    # 매칭 관련
    matching_score = None
    matching_text = None
    matching_explanation = None
    matching_hashtags = []
    is_requested_before = False
    ai_recommendation_reason = None

    # 로그인 청년이면 매칭/요청 여부 계산
    if request.user.is_authenticated and getattr(request.user, "is_youth", False):
        # 점수만 필요한 경우
        matching_score = calculate_matching_score(request.user, owner)
        # 상세 문구/해시태그 등 필요하면 get_matching_details 사용
        try:
            details = get_matching_details(request.user, owner)
            matching_text = details.get("matching_text")
            matching_explanation = details.get("explanation")
            matching_hashtags = details.get("hashtags", [])
            # matching_score가 없으면 details에서 보강
            if matching_score is None:
                matching_score = details.get("matching_score")
        except Exception:
            # 매칭 계산 실패해도 상세 페이지는 떠야 하므로 무시
            pass

        is_requested_before = MoveInRequest.objects.filter(
            youth=request.user, room=room
        ).exists()

        # 세션에 저장해둔 AI 추천 사유
        ai_recommendations = request.session.get('ai_recommendations', {})
        ai_recommendation_reason = ai_recommendations.get(str(room.id))



    ai_summary = "아직 등록된 후기가 없거나, AI 요약 생성에 필요한 데이터가 부족합니다."
    good_hashtags = []
    bad_hashtags = []

    # 리뷰/평점
    reviews = Review.objects.filter(room=room).order_by('-created_at')
    review_count = reviews.count()

    review_texts_list = []
    for review in reviews:
        if review.good_points:
            review_texts_list.append(review.good_points)
        if review.bad_points:
            review_texts_list.append(review.bad_points)

    review_texts = " ".join(review_texts_list)

    if review_texts:
        prompt = f"""
                아래 후기 텍스트들을 분석하여 전체 내용을 50자 이내로 간결하게 요약해줘.
                요약 내용은 그저 나열식이 아니라 깔끔하게 정리된 문장이어야 해. 존댓말을 사용해.
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
            if "```json" in response.text:
                response_text = response.text.split("```json")[1].split("```")[0]
            else:
                response_text = response.text
            ai_data = json.loads(response_text.strip())

            ai_summary = ai_data.get('summary', ai_summary)
            good_hashtags = ai_data.get('good_hashtags', good_hashtags)
            bad_hashtags = ai_data.get('bad_hashtags', bad_hashtags)

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
            output_field=models.IntegerField(),
        )
    )
    average_rating = reviews_with_scores.aggregate(
        Avg('satisfaction_score')
    )['satisfaction_score__avg'] or 0.0


    context = {
        "room": room,
        "matching_score": matching_score,             # int or None
        "matching_text": matching_text,               # 예: "매우 잘 맞음 👍"
        "matching_explanation": matching_explanation, # 예: "'생활리듬'과 '대화스타일'이 잘 맞아요."
        "matching_hashtags": matching_hashtags,       # 예: ["아침형","깔끔한","비흡연"]
        "is_requested_before": is_requested_before,
        "ai_recommendation_reason": ai_recommendation_reason,

        # 리뷰 관련
        "reviews": reviews,
        "review_count": review_count,
        "average_rating": average_rating,
        "ai_summary": ai_summary,
        "good_hashtags": good_hashtags,
        "bad_hashtags": bad_hashtags,
    }
    return render(request, 'room/room_detail.html', context)


@login_required
def senior_request_inbox(request):
    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')
        # 시니어 전용 페이지 (청년이면 리다이렉트)
    if getattr(request.user, "is_youth", False):
        return render(request, 'users/re_login.html')

    senior_rooms = Room.objects.filter(owner=request.user)
    requests = (
        MoveInRequest.objects
        .filter(room__in=senior_rooms)
        .select_related("room", "youth")   # N+1 방지
        .order_by("-requested_at")
    )

    context = {
        'requests': requests,
    }
    return render(request, 'room/senior_request_inbox.html', context)


def all_reviews_for_room(request, room_id):
    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')
    if not getattr(request.user, "is_youth", False):
        return render(request, 'users/re_login.html')

    room = get_object_or_404(Room, id=room_id)
    reviews = Review.objects.filter(room=room).order_by('-created_at')

    context = {
        'room': room,
        'reviews': reviews,
    }
    return render(request, 'room/all_reviews_for_room.html', context)