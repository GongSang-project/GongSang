from django import forms
from .models import Room, OPTION_CHOICES, SECURITY_CHOICES, OTHER_FACILITY_CHOICES, HEATING_CHOICES

# 0) 등기부 업로드(촬영/첨부 공용)
class DeedUploadRawForm(forms.Form):
    file = forms.FileField()

    def clean_file(self):
        f = self.cleaned_data["file"]
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError("파일은 10MB 이하만 업로드 가능합니다.")
        name = (f.name or "").lower()
        ctype = getattr(f, "content_type", "")
        ok = name.endswith((".jpg", ".jpeg", ".png", ".webp", ".pdf")) or ctype in {
            "image/jpeg", "image/png", "image/webp", "application/pdf"
        }
        if not ok:
            raise forms.ValidationError("이미지 또는 PDF만 업로드 가능합니다.")
        return f

# 1) 주소
class RoomStepAddressForm(forms.Form):
    address_province  = forms.CharField(label="시/도")
    address_city      = forms.CharField(label="구/군")
    address_district  = forms.CharField(label="동/읍/면")
    address_detailed  = forms.CharField(label="상세주소")
    nearest_subway    = forms.CharField(label="가까운 지하철역", required=False)

# 2) 상세
class RoomStepDetailForm(forms.Form):
    floor      = forms.CharField(label="층수")              # ex) "아파트 9층"
    area       = forms.FloatField(label="면적(m²)", min_value=0.1)
    toilet_count = forms.IntegerField(label="화장실 개수", min_value=1)

# 3) 거래
class RoomStepContractForm(forms.Form):
    can_short_term = forms.BooleanField(label="단기 거주 가능", required=False)
    rent_fee    = forms.IntegerField(label="월세/사용료(만원)", min_value=0)
    utility_fee = forms.IntegerField(label="관리비(만원)", min_value=0, required=False)
    deposit     = forms.IntegerField(label="보증금(만원)", min_value=0)

# 4) 기간
class RoomStepPeriodForm(forms.Form):
    available_date = forms.DateField(label="입주 가능일", widget=forms.DateInput(attrs={"type":"date"}))


class RoomEditForm(forms.ModelForm):
    # JSONField 들은 MultipleChoiceField 로 받아서 list 로 저장
    options = forms.MultipleChoiceField(
        choices=OPTION_CHOICES, required=False, widget=forms.CheckboxSelectMultiple
    )
    security_facilities = forms.MultipleChoiceField(
        choices=SECURITY_CHOICES, required=False, widget=forms.CheckboxSelectMultiple
    )
    other_facilities = forms.MultipleChoiceField(
        choices=OTHER_FACILITY_CHOICES, required=False, widget=forms.CheckboxSelectMultiple
    )
    heating_type = forms.ChoiceField(
        choices=[("", "선택 안 함")] + list(HEATING_CHOICES), required=False
    )
    available_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = Room
        fields = [
            "deposit", "rent_fee", "utility_fee",
            "floor", "area", "toilet_count", "available_date",
            "address_province", "address_city", "address_district", "address_detailed",
            "nearest_subway",
            "options", "security_facilities", "other_facilities",
            "parking_available", "pet_allowed", "heating_type", "can_short_term",
        ]