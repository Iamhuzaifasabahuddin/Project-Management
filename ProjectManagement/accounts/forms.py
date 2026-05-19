# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    # user enters ONLY username part
    email = forms.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2'
        ]

    def clean_email(self):

        ALLOWED_DOMAIN = "topsoftdigitals.pk"

        email_part = self.cleaned_data.get("email", "").strip().lower()

        # prevent user typing full email
        if "@" in email_part:
            raise forms.ValidationError(
                "Only enter the email username, not the domain."
            )

        full_email = f"{email_part}@{ALLOWED_DOMAIN}"

        if User.objects.filter(email=full_email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return full_email