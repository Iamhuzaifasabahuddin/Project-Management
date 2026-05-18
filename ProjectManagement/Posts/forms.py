from django import forms
from .models import Post, Comment, PostFile, CommentFile


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