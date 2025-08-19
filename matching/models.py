from django.db import models
from users.models import User
from room.models import Room

class MoveInRequest(models.Model):
    youth = models.ForeignKey(User, on_delete=models.CASCADE, related_name='move_in_requests_as_youth')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='move_in_requests_for_room')
    is_contacted = models.BooleanField(default=False, verbose_name="연락처 확인 여부")
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.youth.username} -> {self.room.id} (contacted: {self.is_contacted})"