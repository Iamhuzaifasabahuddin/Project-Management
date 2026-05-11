# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Workspace, Membership, Post, Comment, Client


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


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ['name']


class RoleAssignForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['user', 'workspace', 'role']

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        workspace = cleaned_data.get("workspace")
        role = cleaned_data.get("role")

        if Membership.objects.filter(
                user=user,
                workspace=workspace,
                role=role
        ).exists():
            raise forms.ValidationError(
                "This role is already assigned to this user in this workspace."
            )

        return cleaned_data


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'file']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'file']


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'address', 'number', 'email', 'paid', 'amount_paid', 'paid_type', 'payment_date',
                  'total_amount', 'assigned_to']
