from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.postgres.fields import ArrayField


class User(AbstractUser):
    USERNAME_FIELD = 'username'
    is_youth = models.BooleanField(default=True) #T면 청년, F면 시니어
    profile_image = models.ImageField(
        "프로필 이미지", upload_to="users/profile", blank=True)
    is_id_verified = models.BooleanField(default=False) #신분증 인증 여부
    age = models.IntegerField(default=20, null=True, blank=True) #나이
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True) #성별
    phone_number = models.CharField(max_length=11, blank=True, null=True) #전화번호

    # 뷰 함수에 쓸 하이픈 포함 전화번호 띄우기
    # def format_phone_number(number_str):
    #     if len(number_str) == 11:
    #         return f"{number_str[:3]}-{number_str[3:7]}-{number_str[7:]}"
    #     return number_str


    id_card_image = models.ImageField(
        "신분증 사진",
        upload_to="users/id_card",  # 파일이 저장될 경로 (MEDIA_ROOT/users/id_card)
        blank=True,
        null=True
    )
    is_id_card_uploaded = models.BooleanField("신분증 첨부 여부", default=False)

    #설문 1 - 활동 시간대
    TIME_CHOICES = [
        ('A', '🌅 아침형'),
        ('B', '🌙 저녁형'),
    ]
    preferred_time = models.CharField(max_length=1, choices=TIME_CHOICES, null=True, blank=True)

    #설문 2 - 대화 스타일
    STYLE_CHOICES = [
        ('A', '🤫 필요한 대화만'),
        ('B', '💬 자주 대화'),
    ]
    conversation_style = models.CharField(max_length=1, choices=STYLE_CHOICES, null=True, blank=True)

    #설문 3 - 중요한 점
    IMPORTANT_CHOICES = [
        ('A', '🧹 청결'),
        ('B', '🛌 생활 리듬'),
        ('C', '🧍 소통'),
        ('D', '🙋 배려심'),
        ('E', '🔏 사생활 존중'),
    ]
    important_points = models.TextField(
        blank=True,
        null=True,
        verbose_name='생활 공간에서 가장 중요하게 생각하는 점'
    )

    #설문 4 - 식사
    MEAL_CHOICES = [
        ('A', '	🍽️ 함께 먹기 좋아해요'),
        ('B', '🍱 각자 먹기 선호해요'),
    ]
    meal_preference = models.CharField(max_length=1, choices=MEAL_CHOICES, null=True, blank=True)

    #설문 5 - 주말
    WEEKEND_CHOICES = [
        ('A', '🏠 집에서'),
        ('B', '🚶 외출'),
    ]
    weekend_preference = models.CharField(max_length=1, choices=WEEKEND_CHOICES, null=True, blank=True)

    #설문 6 - 흡연
    SMOKING_CHOICES = [
        ('A', '🚬 예'),
        ('B', '🚭 아니오'),
    ]
    smoking_preference = models.CharField(max_length=1, choices=SMOKING_CHOICES, null=True, blank=True)

    #설문 7 - 소음 발생
    NOISE_CHOICES = [
        ('A', '📺 하루 종일 틀어놓는 편이에요'),
        ('B', '🎶 특정 시간대만 들어요'),
        ('C', '🔇 거의 안 켜요'),
    ]
    noise_level = models.CharField(max_length=1, choices=NOISE_CHOICES, null=True, blank=True)

    #설문 8 - 공간 공유
    SPACE_CHOICES = [
        ('A', '자주 이용'),
        ('B', '필요할 때만'),
        ('C', '거의 이용 안 함'),
    ]
    space_sharing_preference = models.CharField(max_length=1, choices=SPACE_CHOICES, null=True, blank=True)

    #설문 9 - 반려동물
    PET_CHOICES = [
        ('A', '🐶 가능'),
        ('B', '🐱 불가능'),
    ]
    pet_preference = models.CharField(max_length=1, choices=PET_CHOICES, null=True, blank=True)

    #설문 10 - 바라는 점 (서술형)
    wishes = models.TextField(blank=True, null=True)

    interested_province = models.CharField(max_length=50, blank=True, null=True, verbose_name="관심 시/도")
    interested_city = models.CharField(max_length=50, blank=True, null=True, verbose_name="관심 시/군/구")
    interested_district = models.CharField(max_length=50, blank=True, null=True, verbose_name="관심 읍/면/동")

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='youth',
        blank=True,
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='youth',
        blank=True,
        verbose_name='user permissions',
    )

    class LivingType(models.TextChoices):
        ALONE_FEMALE_SENIOR = "alone_female_senior", "혼자"
        SENIOR_COUPLE = "senior_couple", "시니어 부부"
        GRANDCHILD = "grandchild", "손자"

    living_type = models.CharField(
        max_length=30,
        choices=LivingType.choices,
        blank=True,
        null=True,
        verbose_name="동거 형태"
    )

    living_type_other = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="기타 동거 형태"
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'