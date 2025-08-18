from django import forms
from .models import User

# 1. 기본정보
class UserInformationForm(forms.ModelForm):
    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        widget=forms.RadioSelect,
        label='성별'
    )
    class Meta:
        model = User
        fields = ['username', 'gender', 'age', 'phone_number']

# 1-2. (시니어) 동거형태
class SeniorLivingTypeForm(forms.ModelForm):
    living_type = forms.ChoiceField(
        choices=User.LivingType.choices,
        widget=forms.RadioSelect,
        label='동거 형태',
        required = False
    )
    living_type_other = forms.CharField(
        label='기타 (직접 입력)',
        max_length=100,
        required=False
    )

    class Meta:
        model = User
        fields = ['living_type', 'living_type_other']

    def clean(self):
        cleaned_data = super().clean()
        living_type = cleaned_data.get('living_type')
        living_type_other = cleaned_data.get('living_type_other')

        # 라디오 버튼 또는 기타 입력란 중 하나라도 값이 있어야 넘어가도록
        if not living_type and not living_type_other:
            raise forms.ValidationError("동거 형태를 선택하거나 직접 입력해 주세요.")

        return cleaned_data

# 2. 신분증 업로드
class IdCardForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id_card_image']
        widgets = {
            'id_card_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

# 3. 성향조사
class SurveyStep1Form(forms.Form):
    preferred_time = forms.ChoiceField(
        choices=User.TIME_CHOICES,
        widget=forms.RadioSelect,
        label='하루 중 가장 활동적인 시간대는 언제인가요?',
        required=False
    )

class SurveyStep2Form(forms.Form):
    conversation_style = forms.ChoiceField(
        choices=User.STYLE_CHOICES,
        widget=forms.RadioSelect,
        label='함께 지내는 분과의 대화는 어느 정도가 좋으세요?',
        required=False
    )

class SurveyStep3Form(forms.Form):
    important_points = forms.MultipleChoiceField(
        choices=User.IMPORTANT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='생활 공간에서 가장 중요하게 생각하는 점은 무엇인가요? (최대 2개 선택)',
        required=False
    )

    def clean_important_points(self):
        selected_points = self.cleaned_data.get('important_points')

        if selected_points and len(selected_points) > 2:
            raise forms.ValidationError('최대 2개의 항목만 선택할 수 있습니다.')

        return selected_points


class SurveyStep4Form(forms.Form):
    meal_preference = forms.ChoiceField(
        choices=User.MEAL_CHOICES,
        widget=forms.RadioSelect,
        label='음식을 함께 나눠 먹는 것에 대해 어떻게 생각하시나요?',
        required=False
    )

class SurveyStep5Form(forms.Form):
    weekend_preference = forms.ChoiceField(
        choices=User.WEEKEND_CHOICES,
        widget=forms.RadioSelect,
        label='주말에는 주로 어떻게 시간을 보내세요?',
        required=False
    )


class SurveyStep6Form(forms.Form):
    smoking_preference = forms.ChoiceField(
        choices=User.SMOKING_CHOICES,
        widget=forms.RadioSelect,
        label='흡연 여부를 선택해주세요.',
        required=False
    )


class SurveyStep7Form(forms.Form):
    noise_level = forms.ChoiceField(
        choices=User.NOISE_CHOICES,
        widget=forms.RadioSelect,
        label='TV, 음악, 통화 등의 생활 소음에 대해 어떻게 생각하세요?',
        required=False
    )


class SurveyStep8Form(forms.Form):
    space_sharing_preference = forms.ChoiceField(
        choices=User.SPACE_CHOICES,
        widget=forms.RadioSelect,
        label='공용공간(거실, 주방 등)을 얼마나 자주 사용하세요?',
        required=False
    )

class SurveyStep9Form(forms.Form):
    pet_preference = forms.ChoiceField(
        choices=User.PET_CHOICES,
        widget=forms.RadioSelect,
        label='반려동물과 함께 지내는 것에 대해 어떻게 생각하세요?',
        required=False
    )

class SurveyStep10Form(forms.Form):
    wishes = forms.CharField(
        widget=forms.Textarea,
        label='함께 살게 될 청년(또는 어르신)에게 바라는 점이 있다면 자유롭게 적어주세요. (선택 응답)',
        required=False,
    )

# 4. (청년) 지역조사
class YouthInterestedRegionForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['interested_province', 'interested_city', 'interested_district']