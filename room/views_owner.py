# room/views_owner.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django import forms
from django.db.models import Prefetch

from .models import Room

# ✅ RoomPhoto는 선택적으로 import
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
        # ✅ RoomPhoto의 실제 역참조 이름을 안전하게 얻기 (related_name이 무엇이든 동작)
        rel_name = RoomPhoto._meta.get_field("room").remote_field.get_accessor_name()
        photos_qs = RoomPhoto.objects.only("id", "image", "category", "room_id").order_by("id")
        rooms = base_qs.prefetch_related(Prefetch(rel_name, queryset=photos_qs, to_attr="photos"))
    else:
        # ✅ 사진 모델이 없을 때도 템플릿이 깨지지 않도록 빈 리스트 주입
        rooms = list(base_qs)
        for r in rooms:
            r.photos = []

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
