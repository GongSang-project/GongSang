from django import forms
from .models import User

class SurveyStep1Form(forms.Form):
    preferred_time = forms.ChoiceField(
        choices=User.TIME_CHOICES,
        widget=forms.RadioSelect,
        label='하루 중 가장 활동적인 시간대는 언제인가요?'
    )

class SurveyStep2Form(forms.Form):
    conversation_style = forms.ChoiceField(
        choices=User.STYLE_CHOICES,
        widget=forms.RadioSelect,
        label='함께 지내는 분과의 대화는 어느 정도가 좋으세요?'
    )

class SurveyStep3Form(forms.Form):
    important_points = forms.ChoiceField(
        choices=User.IMPORTANT_CHOICES,
        widget=forms.RadioSelect,
        label='생활 공간에서 가장 중요하게 생각하는 점은 무엇인가요? (최대 2개 선택)'
    )


class SurveyStep4Form(forms.Form):
    meal_preference = forms.ChoiceField(
        choices=User.MEAL_CHOICES,
        widget=forms.RadioSelect,
        label='음식을 함께 나눠 먹는 것에 대해 어떻게 생각하시나요?'
    )

class SurveyStep5Form(forms.Form):
    weekend_preference = forms.ChoiceField(
        choices=User.WEEKEND_CHOICES,
        widget=forms.RadioSelect,
        label='주말에는 주로 어떻게 시간을 보내시나요?'
    )


class SurveyStep6Form(forms.Form):
    smoking_preference = forms.ChoiceField(
        choices=User.SMOKING_CHOICES,
        widget=forms.RadioSelect,
        label='흡연 여부를 선택해주세요.'
    )


class SurveyStep7Form(forms.Form):
    noise_level = forms.ChoiceField(
        choices=User.NOISE_CHOICES,
        widget=forms.RadioSelect,
        label='TV, 음악, 통화 등의 생활 소음에 대해 어떻게 생각하세요?'
    )


class SurveyStep8Form(forms.Form):
    space_sharing_preference = forms.ChoiceField(
        choices=User.SPACE_CHOICES,
        widget=forms.RadioSelect,
        label='공용공간(거실, 주방 등)을 사용하는 것에 대해 어떻게 생각하시나요?'
    )

class SurveyStep9Form(forms.Form):
    pet_preference = forms.ChoiceField(
        choices=User.PET_CHOICES,
        widget=forms.RadioSelect,
        label='반려동물과 함께 지내는 것에 대해 어떻게 생각하시나요?'
    )

class SurveyStep10Form(forms.Form):
    wishes = forms.CharField(
        widget=forms.Textarea,
        label='함께 살게 될 청년(또는 어르신)에게 바라는 점이 있다면 자유롭게 적어주세요. (선택 응답)',
        required=False,
    )