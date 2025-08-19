from django import forms
from .models import Review, LIVED_PERIOD_CHOICES, SATISFACTION_CHOICES, RE_LIVING_CHOICES


class ReviewFormStep1(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['contract_document']
        widgets = {'contract_document': forms.FileInput()}


class ReviewFormStep2(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['lived_period']
        widgets = {'lived_period': forms.RadioSelect(choices=LIVED_PERIOD_CHOICES)}


class ReviewFormStep3(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['satisfaction']
        widgets = {'satisfaction': forms.RadioSelect(choices=SATISFACTION_CHOICES)}


class ReviewFormStep4(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['good_points']
        widgets = {'good_points': forms.Textarea(attrs={'rows': 5})}


class ReviewFormStep5(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['bad_points']
        widgets = {'bad_points': forms.Textarea(attrs={'rows': 5})}


class ReviewFormStep6(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['re_living_hope', 'is_anonymous']
        widgets = {'re_living_hope': forms.RadioSelect(choices=RE_LIVING_CHOICES)}