from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django_select2.forms import Select2MultipleWidget, Select2Widget

from workspaces.models import Workspace, Membership, Client


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if Workspace.objects.filter(name__iexact=name).exists():
            raise ValidationError(f"A workspace with the name {name} already exists.")

        return name


class RoleAssignForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=Select2MultipleWidget(attrs={
            'class': 'form-control',
            'data-placeholder': 'Select one or more users...',
            'data-allow-clear': 'true',
            'data-close-on-select': False,
        }),
        help_text="Select one or more users to assign this role to."
    )
    workspace = forms.ModelChoiceField(
        queryset=Workspace.objects.all(),
        widget=Select2Widget(attrs={
            'class': 'form-control',
            'data-placeholder': 'Select target workspace...',
        })
    )
    role = forms.ChoiceField(
        choices=Membership.ROLE_CHOICES,
        widget=Select2Widget(attrs={
            'class': 'form-control',
            'data-placeholder': 'Select designated role...',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        users = cleaned_data.get("users")
        workspace = cleaned_data.get("workspace")
        role = cleaned_data.get("role")

        if users and workspace and role:
            existing = Membership.objects.filter(
                user__in=users,
                workspace=workspace,
                role=role
            ).values_list('user__username', flat=True)

            if existing.exists():
                usernames = ", ".join(existing)
                raise forms.ValidationError(
                    f"The following users already have this role in this workspace: {usernames}"
                )

        return cleaned_data


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'creation_date', 'notes', 'assigned_to']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter client name',
                'autocomplete': 'off',
            }),
            'creation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notes',
                'autocomplete': 'off',
            }),
            'assigned_to': Select2MultipleWidget(attrs={
                'class': 'form-control',
                'data-placeholder': 'Search and select users...',
                'data-allow-clear': 'true',
                'data-minimum-input-length': 0,
                'data-close-on-select': False,
            }),
        }

    def __init__(self, *args, **kwargs):
        workspace = kwargs.pop('workspace', None)
        super().__init__(*args, **kwargs)
        
        if workspace:
            self.fields['assigned_to'].queryset = User.objects.filter(
                membership__workspace=workspace
            ).distinct()
        
        self.fields['assigned_to'].label_from_instance = self._user_label
        self.fields['assigned_to'].required = True
        self.fields['assigned_to'].help_text = 'Use CTRL key to select one or more users to assign this client'
        self.fields['notes'].required = False

    @staticmethod
    def _user_label(user):
        """Display user's full name or username"""
        full_name = user.get_full_name()
        return full_name if full_name.strip() else user.username


class ClientEditForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'address', 'number', 'email', 'total_amount', 'amount_paid', 'payment_date', 'paid_type'
                  ,'paid', 'creation_date', 'notes', 'assigned_to']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter client name',
                'autocomplete': 'off',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address',
                'autocomplete': 'off',
            }),
            'number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
                'autocomplete': 'off',
                'minlength': '10',
                'maxlength': '15',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address',
                'autocomplete': 'email',
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'paid_type': Select2Widget(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select payment type...',
                'data-allow-clear': 'true',
            }),
            'paid': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'creation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notes',
                'autocomplete': 'off',
            }),
            'assigned_to': Select2MultipleWidget(attrs={
                'class': 'form-control',
                'data-placeholder': 'Search and select users...',
                'data-allow-clear': 'true',
                'data-minimum-input-length': 0,
                'data-close-on-select': False,
            }),
        }

    def __init__(self, *args, **kwargs):
        workspace = kwargs.pop('workspace', None)
        super().__init__(*args, **kwargs)
        
        if workspace:
            self.fields['assigned_to'].queryset = User.objects.filter(
                membership__workspace=workspace
            ).distinct()
        
        self.fields['assigned_to'].label_from_instance = self._user_label
        self.fields['assigned_to'].required = True
        self.fields['assigned_to'].help_text = 'Use CTRL key to select one or more users to assign this client'
        self.fields['notes'].required = False
        self.fields['payment_date'].required = False
        self.fields['amount_paid'].help_text = 'Amount the client has paid so far'
        self.fields['total_amount'].help_text = 'Total amount owed by the client'

        # Add validators to number field
        self.fields['number'].validators.extend([
            MinLengthValidator(10, message='Phone number must be at least 10 digits'),
            MaxLengthValidator(15, message='Phone number cannot exceed 15 digits'),
        ])

    @staticmethod
    def _user_label(user):
        """Display user's full name or username"""
        full_name = user.get_full_name()
        return full_name if full_name.strip() else user.username

    def clean_email(self):
        """Validate that email doesn't already exist"""
        email = self.cleaned_data.get('email')

        if not email:
            return email
        query = Client.objects.filter(email__icontains=email)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError(
                f"A client with the email '{email}' already exists."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        total = cleaned_data.get("total_amount")
        paid_amount = cleaned_data.get("amount_paid")

        if total is not None and paid_amount is not None:

            if paid_amount > total:
                raise forms.ValidationError(
                    "Amount paid cannot be greater than total amount."
                )

            cleaned_data["paid"] = (paid_amount == total)

        return cleaned_data