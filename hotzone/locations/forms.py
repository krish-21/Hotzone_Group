from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm


from .models import StaffUser, Location


class StuffUserCreationForm(UserCreationForm):
    class Meta:
        model = StaffUser
        fields = '__all__'

class LocationForm(forms.Form):
    name = forms.CharField(label='Location', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))

class AddVisitForm(forms.Form):
    # iterable 
    VISIT_TYPES =( 
        ("Visit", "Visit"), 
        ("Residence", "Residence"), 
        ("Workplace", "Workplace"), 
    ) 
    datefrom = forms.DateField(label="Date From", widget=forms.SelectDateWidget(years=list(range(2020,1899,-1)), attrs={'class': 'form-control mr-2'}))
    dateto = forms.DateField(label="Date To", widget=forms.SelectDateWidget(years=list(range(2020,1899,-1)), attrs={'class': 'form-control mr-2'}))
    category = forms.CharField(label="Category", max_length=9, widget=forms.Select(choices= VISIT_TYPES, attrs={'class': 'form-control'}))