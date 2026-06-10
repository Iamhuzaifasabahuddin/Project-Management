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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if team:
            qs = team.members.all()
            if user:
                qs = qs.exclude(id=user.id)
            self.fields['assigned_to'].queryset = qs
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


class PrintTaskForm(forms.Form):
    """
    Form for creating a print task.
    """
    FORMAT_CHOICES = (
        ('paperback', 'Paperback'),
        ('hardcover', 'Hardcover'),
        ('coil', 'Coil'),
    )

    client_name = forms.CharField(label="Client Name", disabled=True, required=False)
    brand = forms.CharField(label="Brand", disabled=True, required=False)
    phone_number = forms.CharField(label="Phone Number", disabled=True, required=False)
    number_of_copies = forms.IntegerField(label="Number of Copies", min_value=1)
    format = forms.ChoiceField(label="Format", choices=FORMAT_CHOICES)
    address = forms.CharField(label="Address", widget=forms.Textarea(attrs={'rows': 2}))
    due_date = forms.DateField(
        label="Due Date",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'min': date.today().isoformat(),
        })
    )

    def __init__(self, *args, **kwargs):
        client = kwargs.pop('client', None)
        workspace = kwargs.pop('workspace', None)
        super().__init__(*args, **kwargs)
        
        if client:
            self.fields['client_name'].initial = client.name
            self.fields['phone_number'].initial = client.number
            self.fields['address'].initial = client.address
        if workspace:
            self.fields['brand'].initial = workspace.name
            
        for field in self.fields:
            if field in ['client_name', 'brand', 'phone_number']:
                self.fields[field].widget.attrs.update({'class': 'form-control bg-light'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
