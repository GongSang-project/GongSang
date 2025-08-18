from django.db import models
from django.conf import settings  # settings.AUTH_USER_MODEL을 가져오기 위함
from django.core.validators import MinValueValidator

# 방 옵션
OPTION_CHOICES = [
    ('REFRIGERATOR', '냉장고'),
    ('WASHER', '세탁기'),
    ('SINK', '싱크대'),
    ('DESK', '책상'),
    ('CLOSET', '옷장'),
    ('BUILT_IN_WARDROBE', '붙박이장'),
    ('BED', '침대'),
    ('SHOES', '신발장'),
    ('MICROWAVE', '전자레인지'),
    ('GAS_STOVE', '가스레인지'),
    ('GAS_OVEN', '가스오븐'),
    ('SHOWER_BOOTH', '샤워부스'),
    ('BATHTUB', '욕조'),
    ('BIDET', '비데'),
    ('DRYER', '건조기'),
    ('DISHWASHER', '식기세척기'),
    ('DINING_TABLE', '식탁'),
    ('SOFA', '소파'),
    ('TV', '티비'),
    ('AC', '에어컨'),
    ('FAN', '선풍기'),
    ('INDUCTION', '인덕션'),
    ('WIFI', '와이파이'),
]

# 보안 옵션
SECURITY_CHOICES = [
    ('DOOR_SECURITY', '현관보안'),
    ('CCTV', 'CCTV'),
    ('INTERCOM', '인터폰'),
    ('VIDEOPHONE', '비디오폰'),
    ('CARDKEY', '카드키'),
    ('BURGLAR_BARS', '방범창'),
    ('SELF_SECURITY_GUARD', '자치경비원'),
    ('PRIVATE_SECURITY', '사설경비'),
]

# 기타 시설
OTHER_FACILITY_CHOICES = [
    ('ELEVATOR', '엘리베이터'),
    ('FIRE_ALARM', '화재경보기'),
    ('PARCEL_LOCKER', '무인택배함'),
    ('VERANDA', '베란다'),
    ('TERRACE', '테라스'),
    ('YARD', '마당'),
    ('EXTINGUISHER', '소화기'),
]

# 난방 방식
HEATING_CHOICES = [
    ('INDIVIDUAL', '개별난방'),
    ('CENTRAL', '중앙난방'),
    ('DISTRICT', '지역난방'),
]


class Room(models.Model):
    # 방의 기본 정보
    deposit = models.IntegerField(verbose_name="보증금", validators=[MinValueValidator(0)])
    rent_fee = models.IntegerField(verbose_name="월세", validators=[MinValueValidator(0)])
    floor = models.CharField(verbose_name="층수", max_length=50)  # '아파트 9층', '빌라 2층' 등
    area = models.FloatField(verbose_name="면적(m²)", validators=[MinValueValidator(0.1)])
    utility_fee = models.IntegerField(verbose_name="관리비", default=0, validators=[MinValueValidator(0)])

    # 주소
    address_province = models.CharField(verbose_name="주소(시/도)", max_length=50, blank=True, null=True)
    address_city = models.CharField(verbose_name="주소(시/군/구)", max_length=50, blank=True, null=True)
    address_district = models.CharField(verbose_name="주소(읍/면/동)", max_length=50, blank=True, null=True)
    address_detailed = models.CharField(verbose_name="상세주소(도로명/동/호)", max_length=50, blank=True, null=True)

    # 등기부 등본
    land_register_document = models.FileField(
        verbose_name="등기부 등본",
        upload_to='land_registers/',
        null=True,
        blank=True
    )
    is_land_register_verified = models.BooleanField(
        verbose_name="등기부 등본 인증 여부",
        default=False
    )

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

    # 시설 정보
    options = models.JSONField(verbose_name="생활 시설", default=list)
    security_facilities = models.JSONField(verbose_name="보안 시설", default=list)
    other_facilities = models.JSONField(verbose_name="기타 시설", default=list)

    # 단일 선택 시설
    parking_available = models.BooleanField(verbose_name="주차 가능 여부", default=False)
    pet_allowed = models.BooleanField(verbose_name="반려동물 가능 여부", default=False)
    heating_type = models.CharField(verbose_name="난방 방식", max_length=20, choices=HEATING_CHOICES, blank=True, null=True)

    # 주변 정보
    nearest_subway = models.CharField(verbose_name="주변 지하철역", max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(verbose_name="등록일", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="수정일", auto_now=True)

    def __str__(self):
        full_address = f"{self.address_province} {self.address_city} {self.address_district} {self.address_detailed}"
        return f"{full_address} ({self.owner.username}님의 방)"

    class Meta:
        verbose_name = "방"
        verbose_name_plural = "방 목록"