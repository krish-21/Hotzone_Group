from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm


from .models import StaffUser, Location

class LocationForm(forms.Form):
    name = forms.CharField(label='Location', max_length=100)

class SelectionForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = '__all__'



class StuffUserCreationForm(UserCreationForm):
    class Meta:
        model = StaffUser
        fields = '__all__'