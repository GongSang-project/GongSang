# room/views_owner.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django import forms
from django.urls import reverse

from .models import Room

def _senior_guard(request):
    return request.user.is_authenticated and not getattr(request.user, "is_youth", True)

@login_required
def owner_room_list(request):
    if not _senior_guard(request):
        messages.error(request, "시니어 회원만 접근할 수 있어요.")
        return redirect("users:home_youth")
    rooms = (
        Room.objects.filter(owner=request.user)
        .prefetch_related("photos")     # RoomPhoto.related_name = "photos"
        .order_by("-updated_at", "-created_at")
    )
    return render(request, "room/owner_list.html", {"rooms": rooms})

class RoomOwnerEditForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "deposit","rent_fee","utility_fee","floor","area",
            "toilet_count","available_date","can_short_term",
            "parking_available","pet_allowed","heating_type",
            "nearest_subway",
            "address_province","address_city","address_district","address_detailed",
        ]
        widgets = {"available_date": forms.DateInput(attrs={"type": "date"})}

@login_required
def owner_room_update(request, room_id: int):
    if not _senior_guard(request):
        messages.error(request, "시니어 회원만 접근할 수 있어요.")
        return redirect("users:home_youth")
    # 새 편집 플로우 진입점으로 넘기기
    return redirect("room:edit_start", room_id=room_id)


@login_required
@require_POST
def owner_room_delete(request, room_id: int):
    if not _senior_guard(request):
        messages.error(request, "시니어 회원만 접근할 수 있어요.")
        return redirect("users:home_youth")
    room = get_object_or_404(Room, pk=room_id, owner=request.user)
    room.delete()
    messages.success(request, "방이 삭제되었습니다.")
    return redirect("room:owner_room_list")
