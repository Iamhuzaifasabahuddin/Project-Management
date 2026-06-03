from datetime import date

from django import forms
from django_select2.forms import Select2MultipleWidget

from .models import Post, Comment, PostFile, CommentFile, Task


class TaskForm(forms.ModelForm):
    """
    Form for creating/editing tasks.
    """

    class Meta:
        model = Task
        fields = ['name', 'description', 'due_date', 'assigned_to']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Task name',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write task description here...',
                'rows': 4
            }),
            'assigned_to': Select2MultipleWidget(attrs={
                'class': 'form-control',
                'data-placeholder': 'Search and select users...',
                'data-allow-clear': 'true',
                'data-minimum-input-length': 0,
                'data-close-on-select': False,
            }),

            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().isoformat(),
            })
        }

    def __init__(self, *args, **kwargs):
        team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)
        if team:
            self.fields['assigned_to'].queryset = team.members.all()
        for field in self.fields:
            self.fields[field].required = True


class PostForm(forms.ModelForm):
    """
    Form for creating/editing posts.
    Files are handled separately in the template and view.
    """

    class Meta:
        model = Post
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Post title',
                'maxlength': '255'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your post content here...',
                'rows': 8
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = True


class CommentForm(forms.ModelForm):
    """
    Form for creating/editing comments.
    Files are handled separately in the template and view.
    """

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write a comment...',
                'rows': 4
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = True


class PostFileForm(forms.ModelForm):
    """
    Form for individual file uploads.
    """

    class Meta:
        model = PostFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'allow_multiple_selected': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False


class CommentFileForm(forms.ModelForm):
    """
    Form for individual comment file uploads.
    """

    class Meta:
        model = CommentFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'allow_multiple_selected': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
