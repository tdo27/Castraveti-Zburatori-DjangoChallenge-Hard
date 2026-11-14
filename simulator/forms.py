from django import forms

from .models import Unit


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'type', 'team', 'health', 'attack_points', 'profile_image_link']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Fighter name'}),
            'type': forms.Select(),
            'team': forms.Select(),
            'health': forms.NumberInput(attrs={'min': 0, 'max': Unit.MAX_HEALTH}),
            'attack_points': forms.NumberInput(attrs={'min': 0, 'max': 50}),
            'profile_image_link': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }
