from django.db import models
from django.conf import settings
from room.models import Room
from users.models import User

# 함께 지낸 기간 선택지
LIVED_PERIOD_CHOICES = [
    ('LESS_THAN_1_MONTH', '1개월 미만'),
    ('1_TO_3_MONTHS', '1개월 ~ 3개월'),
    ('3_TO_6_MONTHS', '3개월 ~ 6개월'),
    ('6_TO_12_MONTHS', '6개월 ~ 1년'),
    ('MORE_THAN_1_YEAR', '1년 이상'),
]

# 전반적인 만족도 선택지 (별점)
SATISFACTION_CHOICES = [
    ('VERY_DISSATISFIED', '매우 불만족'),
    ('DISSATISFIED', '불만족'),
    ('NORMAL', '보통'),
    ('SATISFIED', '만족'),
    ('VERY_SATISFIED', '매우 만족'),
]

# 재동거 희망 여부 선택지
RE_LIVING_CHOICES = [
    ('YES', '네, 또 살고 싶어요 😊'),
    ('MAYBE', '상황에 따라 가능할 것 같아요'),
    ('NO', '아니요, 조금 힘들었어요'),
]


class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_written',
                               verbose_name="후기 작성자")
    target_senior = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='reviews_received_senior',
                                      verbose_name="후기 대상(시니어)", null=True, blank=True)
    target_youth = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='reviews_received_youth',
                                     verbose_name="후기 대상(청년)", null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_reviews',
                             verbose_name="후기 대상 방", null=True, blank=True)
    contract_document = models.FileField(verbose_name="임대차 계약서", upload_to='contracts/',
                                         null=True, blank=True)
    lived_period = models.CharField(verbose_name="함께 지낸 기간", max_length=20,
                                    choices=LIVED_PERIOD_CHOICES, default='LESS_THAN_1_MONTH')
    satisfaction = models.CharField(verbose_name="전반적인 만족도", max_length=20,
                                    choices=SATISFACTION_CHOICES, default='NORMAL')
    good_points = models.TextField(verbose_name="좋았던 점", blank=True, null=True)
    bad_points = models.TextField(verbose_name="개선되었으면 하는 점", blank=True, null=True)
    re_living_hope = models.CharField(verbose_name="재동거 희망 여부", max_length=20,
                                     choices=RE_LIVING_CHOICES, default='MAYBE')
    is_anonymous = models.BooleanField(verbose_name="익명으로 후기 작성", default=False)
    created_at = models.DateTimeField(verbose_name="작성일", auto_now_add=True)

    def __str__(self):
        if self.target_senior:
            return f"[{self.room.id}] {self.target_senior.username}에 대한 {self.author.username}의 후기"
        elif self.target_youth:
            return f"[{self.room.id}] {self.target_youth.username}에 대한 {self.author.username}의 후기"
        return "알 수 없는 후기"

    class Meta:
        verbose_name = "후기"
        verbose_name_plural = "후기 목록"
        unique_together = ('author', 'room')