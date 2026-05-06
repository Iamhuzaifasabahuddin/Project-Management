# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Workspace, Membership, Post, Comment


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['first_name', 'last_name','username', 'email', 'password1', 'password2']



class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ['name', 'parent']


class RoleAssignForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['user', 'workspace', 'role']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'file']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'file']
