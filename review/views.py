from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from matching.models import MoveInRequest
from room.models import Room
from django.db.models import Prefetch
from django.urls import reverse
from .models import Review

@login_required
def review_list(request):
    if request.user.is_youth:
        return redirect(reverse('users:home_youth'))

    # 로그인한 시니어 유저가 소유한 방들을 가져옵니다.
    senior_rooms = Room.objects.filter(owner=request.user)

    # 이미 후기를 작성한 청년 목록을 가져옵니다.
    reviewed_youth_ids = Review.objects.filter(
        author=request.user
    ).values_list('youth__id', flat=True)

    # 연락처를 확인했고, 아직 후기를 작성하지 않은 청년 목록을 가져옵니다.
    requested_youth = MoveInRequest.objects.filter(
        room__in=senior_rooms,
        is_contacted=True
    ).exclude(
        youth__id__in=reviewed_youth_ids
    ).order_by('-requested_at').select_related('youth', 'room')

    context = {
        'requested_youth': requested_youth,
    }
    return render(request, 'review/review_list.html', context)

@login_required
def review_completed_list(request):
    """
    작성된 후기가 있는 청년 목록을 보여주는 뷰
    """
    if request.user.is_youth:
        return render(request, 'access_denied.html')

    # 현재 로그인된 시니어 유저가 작성한 후기들을 가져옵니다.
    completed_reviews = Review.objects.filter(author=request.user).select_related('youth', 'room')

    context = {
        'completed_reviews': completed_reviews,
    }
    return render(request, 'review/review_completed_list.html', context)
