# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

    def clean_email(self):
        ALLOWED_DOMAIN = "topsoftdigitals.pk"
        email = self.cleaned_data.get("email", "").strip().lower()

        if not email.endswith(f"@{ALLOWED_DOMAIN}"):
            raise forms.ValidationError(
                f"Only @{ALLOWED_DOMAIN} email addresses are allowed."
            )

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")

        return email




