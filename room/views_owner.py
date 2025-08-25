# room/views_owner.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django import forms
from django.db.models import Prefetch

from .models import Room

try:
    from .models import RoomPhoto
except Exception:
    RoomPhoto = None


def _senior_guard(request):
    return request.user.is_authenticated and not getattr(request.user, "is_youth", True)


@login_required
def owner_room_list(request):
    if not _senior_guard(request):
        messages.error(request, "시니어 회원만 접근할 수 있어요.")
        return redirect("users:home_youth")

    base_qs = Room.objects.filter(owner=request.user).order_by("-updated_at", "-created_at")

    if RoomPhoto:
        # related_name = "room_photos" 를 그대로 사용
        photos_qs = RoomPhoto.objects.only("id", "image", "category", "room_id").order_by("id")
        rooms = base_qs.prefetch_related(
            Prefetch("room_photos", queryset=photos_qs)
        )
    else:
        rooms = list(base_qs)  # RoomPhoto 모델이 없을 경우 대비(거의 안 타는 분기)
        for r in rooms:
            r.room_photos = []  # 템플릿에서 room.room_photos.all 호출해도 안전하도록 폴백

    return render(request, "room/owner_list.html", {"rooms": rooms})


class RoomOwnerEditForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "deposit","rent_fee","utility_fee","area",
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

    room = get_object_or_404(Room, pk=room_id, owner=request.user)

    if request.method == "POST":
        form = RoomOwnerEditForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "방 정보가 수정되었습니다.")
            return redirect("room:owner_room_list")
    else:
        form = RoomOwnerEditForm(instance=room)

    return render(request, "room/owner_update.html", {"form": form, "room": room})


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
