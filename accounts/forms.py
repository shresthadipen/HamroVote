from django import forms
from django.core.exceptions import ValidationError

class StudentRegisterForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    registration_number = forms.CharField(max_length=50)
    phone = forms.CharField(max_length=15)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=6)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise ValidationError("Passwords do not match")

        # normalize registration number
        cleaned_data["registration_number"] = (
            cleaned_data.get("registration_number", "").upper().strip()
        )

        return cleaned_data
