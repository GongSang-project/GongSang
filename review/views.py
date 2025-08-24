from django.shortcuts import render, redirect, get_object_or_404
from matching.models import MoveInRequest
from room.models import Room
from django.db.models import Prefetch
from django.urls import reverse
from .models import Review
from .forms import (
    ReviewFormStep1, ReviewFormStep2, ReviewFormStep3,
    ReviewFormStep4, ReviewFormStep5, ReviewFormStep6
)


def review_list_senior(request):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')

    if request.user.is_youth:
        return render(request, 'users/re_login.html')

    # 로그인한 시니어 유저가 소유한 방들
    senior_rooms = Room.objects.filter(owner=request.user)

    # 이미 후기를 작성한 '방' ID 목록
    reviewed_room_ids = Review.objects.filter(
        author=request.user
    ).values_list('room__id', flat=True)

    # 연락처를 확인했고, 아직 후기를 작성하지 않은 방에 대한 요청 목록
    requested_youth = MoveInRequest.objects.filter(
        room__in=senior_rooms,
        is_contacted=True
    ).exclude(
        room__id__in=reviewed_room_ids
    ).order_by('-requested_at').select_related('youth', 'room')

    context = {
        'requested_youth': requested_youth,
    }
    return render(request, 'review/review_list_senior.html', context)


def review_completed_list_senior(request):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')

    if request.user.is_youth:
        return render(request, 'users/re_login.html')

    # 현재 로그인된 시니어 유저가 작성한 후기들
    completed_reviews = Review.objects.filter(author=request.user).select_related('target_youth', 'room')

    context = {
        'completed_reviews': completed_reviews,
    }
    return render(request, 'review/review_completed_list_senior.html', context)


def review_write(request, request_id):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')

    if request.user.is_youth:
        move_in_request = get_object_or_404(MoveInRequest, pk=request_id, youth=request.user)
    else:
        move_in_request = get_object_or_404(MoveInRequest, pk=request_id, room__owner=request.user)

    # 이미 후기를 작성했는지
    is_reviewed = Review.objects.filter(
        author=request.user,
        room=move_in_request.room
    ).exists()

    if is_reviewed:
        if request.user.is_youth:
            return redirect('review:review_completed_list_youth')
        else:
            return redirect('review:review_completed_list_senior')

    if request.method == 'POST':
        form_step1 = ReviewFormStep1(request.POST, request.FILES)
        form_step2 = ReviewFormStep2(request.POST)
        form_step3 = ReviewFormStep3(request.POST)
        form_step4 = ReviewFormStep4(request.POST)
        form_step5 = ReviewFormStep5(request.POST)
        form_step6 = ReviewFormStep6(request.POST)

        # 모든 폼이 유효한지
        if (form_step1.is_valid() and form_step2.is_valid() and form_step3.is_valid() and
                form_step4.is_valid() and form_step5.is_valid() and form_step6.is_valid()):
            # 모든 데이터를 하나의 객체로 저장
            review_data = {
                'author': request.user,
                'room': move_in_request.room,
                **form_step1.cleaned_data,
                **form_step2.cleaned_data,
                **form_step3.cleaned_data,
                **form_step4.cleaned_data,
                **form_step5.cleaned_data,
                **form_step6.cleaned_data,
            }

            if request.user.is_youth:
                review_data['target_senior'] = move_in_request.room.owner
            else:
                review_data['target_youth'] = move_in_request.youth

            Review.objects.create(**review_data)

            if request.user.is_youth:
                return redirect('review:review_completed_list_youth')
            else:
                return redirect('review:review_completed_list_senior')
    else:
        form_step1 = ReviewFormStep1()
        form_step2 = ReviewFormStep2()
        form_step3 = ReviewFormStep3()
        form_step4 = ReviewFormStep4()
        form_step5 = ReviewFormStep5()
        form_step6 = ReviewFormStep6()

    context = {
        'form1': form_step1,
        'form2': form_step2,
        'form3': form_step3,
        'form4': form_step4,
        'form5': form_step5,
        'form6': form_step6,
        'youth': move_in_request.youth,
        'room': move_in_request.room,
        'request_id': request_id,
    }
    return render(request, 'review/review_write_all.html', context)


def review_list_youth(request):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')

    if not request.user.is_youth:
        return render(request, 'users/re_login.html')

    reviewed_room_ids = Review.objects.filter(
        author=request.user
    ).values_list('room__id', flat=True)

    reviewable_requests = MoveInRequest.objects.filter(
        youth=request.user,  # 요청을 보낸 청년이 현재 로그인한 유저
        is_contacted=True  # 시니어가 청년의 연락처를 확인함
    ).exclude(
        room__id__in=reviewed_room_ids  # 이미 후기를 작성한 방은 제외
    ).order_by('-requested_at').select_related('room', 'room__owner')

    context = {
        'reviewable_requests': reviewable_requests,
    }
    return render(request, 'review/review_list_youth.html', context)


def review_completed_list_youth(request):

    if not request.user.is_authenticated:
        return render(request, 'users/re_login.html')

    if not request.user.is_youth:
        return render(request, 'users/re_login.html')

    # 현재 로그인된 청년 유저가 작성한 후기들
    completed_reviews = Review.objects.filter(
        author=request.user
    ).select_related('room', 'room__owner', 'target_senior')

    context = {
        'completed_reviews': completed_reviews,  # 작성 완료된 후기 목록
    }
    return render(request, 'review/review_completed_list_youth.html', context)