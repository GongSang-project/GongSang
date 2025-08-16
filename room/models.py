from django.db import models
from django.conf import settings  # settings.AUTH_USER_MODEL을 가져오기 위함
from django.core.validators import MinValueValidator

# 방 옵션
OPTION_CHOICES = [
    ('AC', '에어컨'),
    ('SHOES', '신발장'),
    ('CLOSET', '옷장'),
    ('FRIDGE', '냉장고'),
    ('WASHER', '세탁기'),
    ('MICROWAVE', '전자레인지'),
    ('INDUCTION', '인덕션'),
    ('BED', '침대'),
    ('DESK', '책상'),
    ('WIFI', '와이파이'),
]

# 보안 옵션
SECURITY_CHOICES = [
    ('INTERCOM', '인터폰'),
    ('CCTV', 'CCTV'),
    ('DOOR_SECURITY', '현관보안'),
]


class Room(models.Model):
    # 방의 기본 정보
    deposit = models.IntegerField(verbose_name="보증금", validators=[MinValueValidator(0)])
    rent_fee = models.IntegerField(verbose_name="월세", validators=[MinValueValidator(0)])
    address = models.CharField(verbose_name="주소", max_length=200)
    floor = models.CharField(verbose_name="층수", max_length=50)  # '아파트 9층', '빌라 2층' 등
    area = models.FloatField(verbose_name="면적(m²)", validators=[MinValueValidator(0.1)])
    utility_fee = models.IntegerField(verbose_name="관리비", default=0, validators=[MinValueValidator(0)])

    # 주소
    address_province = models.CharField(verbose_name="주소(시/도)", max_length=50, blank=True, null=True)
    address_city = models.CharField(verbose_name="주소(시/군/구)", max_length=50, blank=True, null=True)
    address_district = models.CharField(verbose_name="주소(읍/면/동)", max_length=50, blank=True, null=True)

    # 추가 정보
    can_short_term = models.BooleanField(verbose_name="단기 거주 가능 여부", default=False)
    toilet_count = models.IntegerField(verbose_name="화장실 개수", default=1, validators=[MinValueValidator(1)])
    available_date = models.DateField(verbose_name="입주 가능일")

    # 소유주 및 계약 정보
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_rooms',
                              verbose_name="소유주(시니어 회원)")
    contracted_youth = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='contracted_rooms', verbose_name="계약한 청년 회원")

    # 집 주인의 정보 (시니어)
    owner_living_status = models.CharField(verbose_name="거주 형태", max_length=50, blank=True,
                                           null=True)  # '부부 거주', '혼자 거주' 등

    # 방 상세페이지에 해시태그 표시하는 과정은 room/views.py 파일 room_detail()에 정의되어 있습니다
    # room_detail() 함수에다가 방 상세페이지에 띄울 정보들 더 추가하시면 됩니다!

    # AI 분석 결과
    ai_analysis_result1 = models.CharField(verbose_name="AI 분석 결과 1", max_length=200, blank=True, null=True)
    ai_analysis_result2 = models.CharField(verbose_name="AI 분석 결과 2", max_length=200, blank=True, null=True)
    ai_matching_score = models.IntegerField(verbose_name="AI 매칭 점수", default=0, validators=[MinValueValidator(0)])

    # 시설 정보
    options = models.JSONField(verbose_name="옵션", default=list)  # ['에어컨', '신발장'] 등 리스트로 저장
    security_facilities = models.JSONField(verbose_name="보안시설", default=list)  # ['인터폰', 'CCTV'] 등 리스트로 저장

    # 주변 정보
    nearest_subway = models.CharField(verbose_name="주변 지하철역", max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(verbose_name="등록일", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="수정일", auto_now=True)

    def __str__(self):
        return f"{self.address} ({self.owner.username}님의 방)"

    class Meta:
        verbose_name = "방"
        verbose_name_plural = "방 목록"