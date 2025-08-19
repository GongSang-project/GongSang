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