from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from room.models import Room
from .models import MoveInRequest
from users.models import User
from .utils import calculate_matching_score, WEIGHTS
from django.urls import reverse


@require_POST
@login_required
def request_move_in(request, room_id):
    if not request.user.is_youth:
        return redirect(reverse('users:home_youth'))

    try:
        room = get_object_or_404(Room, pk=room_id)
        youth_user = request.user

        if MoveInRequest.objects.filter(youth=youth_user, room=room).exists():
            return redirect(reverse('room:room_detail', args=[room_id]))

        MoveInRequest.objects.create(youth=youth_user, room=room)

        return redirect(reverse('room:room_detail', args=[room_id]))

    except Exception as e:
        return redirect(reverse('room:room_detail', args=[room_id]))


@require_POST
@login_required
def confirm_contact(request, request_id):
    if request.user.is_youth:
        return redirect(reverse('users:home_youth'))

    try:
        move_in_request = get_object_or_404(MoveInRequest, pk=request_id, room__owner=request.user)

        # is_contacted가 False일 경우에만 업데이트
        if not move_in_request.is_contacted:
            move_in_request.is_contacted = True
            move_in_request.save()
            return JsonResponse({'message': '연락처 확인 상태가 업데이트되었습니다.'}, status=200)
        else:
            return JsonResponse({'message': '이미 확인된 요청입니다.'}, status=200)

    except MoveInRequest.DoesNotExist:
        return JsonResponse({'message': '요청을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'message': f'오류 발생: {str(e)}'}, status=500)