from django import forms
from courses.models import Department, Specialization, SubSpecialization

class DepartmentSelectionForm(forms.Form):
    department = forms.ModelChoiceField(queryset=Department.objects.all(), empty_label='Select a department')

class SpecializationSelectionForm(forms.Form):
    specialization = forms.ModelChoiceField(queryset=Specialization.objects.all(), empty_label='Select a specialization')

class SubSpecializationSelectionForm(forms.Form):
    sub_specialization = forms.ModelChoiceField(queryset=SubSpecialization.objects.all(), empty_label='Select a subspecialization')
