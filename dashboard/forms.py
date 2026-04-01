from django import forms
from voter.models import Election, Position, Candidate
from accounts.models import Student_list

class StudentManualForm(forms.ModelForm):
    class Meta:
        model = Student_list
        fields = ['registration_number', 'full_name']

class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ['title', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input-style', 'placeholder': 'e.g. Student Council 2024'}),
            'description': forms.Textarea(attrs={'class': 'input-style', 'rows': 3}),
            # Use datetime-local so the browser shows a calendar/clock picker
            'start_date': forms.DateTimeInput(attrs={'class': 'input-style', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'input-style', 'type': 'datetime-local'}),
        }

class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['position', 'name', 'bio', 'manifesto', 'photo', 'grade', 'section']