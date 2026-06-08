# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.conf import settings

from .models import User
from Posts.tasks import send_password_reset_email_task

class CustomPasswordResetForm(BasePasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        # Create a serializable copy of the context
        serializable_context = context.copy()
        if 'user' in serializable_context:
            user = serializable_context['user']
            # Replace the User object with its ID
            serializable_context['user_id'] = user.id
            del serializable_context['user']

        # Trigger the async task
        send_password_reset_email_task.delay(
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            context=serializable_context,
            from_email=from_email,
            to_email=to_email,
            html_email_template_name=html_email_template_name
        )


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