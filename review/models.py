from django.db import models
from django.conf import settings
from room.models import Room

class Review(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reviews', verbose_name="방")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="작성자")
    is_anonymous = models.BooleanField(verbose_name="익명 여부", default=True)
    stay_period = models.CharField(verbose_name="거주 기간", max_length=50) 
    content = models.TextField(verbose_name="후기 내용")
    created_at = models.DateTimeField(verbose_name="작성일", auto_now_add=True)

    def __str__(self):
        return f"{self.room.address} - {self.author.username}의 후기"

    class Meta:
        verbose_name = "후기"
        verbose_name_plural = "후기 목록"