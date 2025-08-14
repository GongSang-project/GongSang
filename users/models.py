from django.contrib.auth.models import AbstractUser
from django.db import models


# class Region(models.Model):
#     code = models.CharField(max_length=10, unique=True) #행정동 코드(예: 2112056)
#     name = models.CharField(max_length=50) #행정동 이름(예: 녹산동)
#     region_type = models.CharField(max_length=10, choices=[ #지역 유형 (province, city, district)
#         ('province', '시/도'),
#         ('city', '시/군/구'),
#         ('district', '읍/면/동'),
#     ])
#     parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
#                                related_name='subregions') #상위 지역 (ForeignKey로 상위 지역과 연결)
#
#     def __str__(self):
#         return self.name


class User(AbstractUser):
    USERNAME_FIELD = 'username'
    is_youth = models.BooleanField(default=True) #T면 청년, F면 시니어
    profile_image = models.ImageField(
        "프로필 이미지", upload_to="users/profile", blank=True)
    is_id_verified = models.BooleanField(default=False) #신분증 인증 여부
    age = models.IntegerField(default=20) #나이
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='F') #성별
    affiliation = models.CharField(max_length=100, default='없음') #소속(00대학교)
    introduction = models.TextField(blank=True, null=True) #자기소개

    id_card_image = models.ImageField(
        "신분증 사진",
        upload_to="users/id_card",  # 파일이 저장될 경로 (MEDIA_ROOT/users/id_card)
        blank=True,
        null=True
    )
    is_id_card_uploaded = models.BooleanField("신분증 첨부 여부", default=False)

    land_register = models.ImageField(
        "등기부등본",
        upload_to="users/land_register",
        blank=True,
        null=True
    )
    is_land_register_uploaded = models.BooleanField("등기부등본 첨부 여부", default=False)

    #설문 1 - 활동 시간대
    TIME_CHOICES = [
        ('A', '🌅 아침형'),
        ('B', '🌙 저녁형'),
    ]
    preferred_time = models.CharField(max_length=1, choices=TIME_CHOICES, default='A')

    #설문 2 - 대화 스타일
    STYLE_CHOICES = [
        ('A', '🤫 필요한 대화만'),
        ('B', '💬 자주 대화'),
    ]
    conversation_style = models.CharField(max_length=1, choices=STYLE_CHOICES, default='A')

    #설문 3 - 중요한 점
    IMPORTANT_CHOICES = [
        ('A', '🧹 청결'),
        ('B', '🛌 생활 리듬'),
        ('C', '🧍 소통'),
        ('D', '🙋 배려심'),
        ('E', '🔏 사생활 존중'),
    ]
    important_points = models.CharField(max_length=2, choices=IMPORTANT_CHOICES, default='A')

    #설문 4 - 식사
    MEAL_CHOICES = [
        ('A', '	🍽️ 함께 먹기 좋아해요'),
        ('B', '🍱 각자 먹기 선호해요'),
    ]
    meal_preference = models.CharField(max_length=1, choices=MEAL_CHOICES, default='A')

    #설문 5 - 주말
    WEEKEND_CHOICES = [
        ('A', '🏠 집에서'),
        ('B', '🚶 외출'),
    ]
    weekend_preference = models.CharField(max_length=1, choices=WEEKEND_CHOICES, default='A')

    #설문 6 - 흡연
    SMOKING_CHOICES = [
        ('A', '🚬 예'),
        ('B', '🚭 아니오'),
    ]
    smoking_preference = models.CharField(max_length=1, choices=SMOKING_CHOICES, default='A')

    #설문 7 - 소음 발생
    NOISE_CHOICES = [
        ('A', '📺 하루 종일 틀어놓는 편이에요'),
        ('B', '🎶 특정 시간대만 들어요'),
        ('C', '🔇 거의 안 켜요'),
    ]
    noise_level = models.CharField(max_length=1, choices=NOISE_CHOICES, default='A')

    #설문 8 - 공간 공유
    SPACE_CHOICES = [
        ('A', '자주 이용'),
        ('B', '필요할 때만'),
        ('C', '거의 이용 안 함'),
    ]
    space_sharing_preference = models.CharField(max_length=1, choices=SPACE_CHOICES, default='A')

    #설문 9 - 반려동물
    PET_CHOICES = [
        ('A', '🐶 가능'),
        ('B', '🐱 불가능'),
    ]
    pet_preference = models.CharField(max_length=1, choices=PET_CHOICES, default='A')

    #설문 10 - 바라는 점 (서술형)
    wishes = models.TextField(blank=True, null=True)

    #preferred_regions = models.ManyToManyField(Region, blank=True) #청년 - 지역

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

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'