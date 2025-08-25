from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)  # 예) 서울특별시 노원구 공릉동

    def __str__(self):
        return self.name


class Listing(models.Model):
    title = models.CharField(max_length=200)  # 매물 제목
    price = models.IntegerField()  # 가격
    description = models.TextField(blank=True)  # 설명
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="listings")  # 지역 연결

    def __str__(self):
        return self.title
