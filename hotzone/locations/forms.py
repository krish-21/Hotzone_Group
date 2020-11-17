from django import forms
from django.forms import ModelForm

from .models import Location

class LocationForm(forms.Form):
    name = forms.CharField(label='Location', max_length=100)

class SelectionForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = '__all__'
    