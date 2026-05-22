"""
Fixed Team Forms for Project Management

Implements strict validation, workspace-aware filtering,
and dynamic member management.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django_select2.forms import Select2Widget, Select2MultipleWidget

from workspaces.models import Membership
from Teams.models import Team


# =========================
# TEAM FORM
# =========================

class TeamForm(forms.ModelForm):
    """
    Form for creating and editing teams with multiselect member assignment.
    Workspace-aware user filtering for member selection.

    All fields are required: name, team_lead, members, roles
    """

    # Explicitly define members as ModelMultipleChoiceField
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),  # Set in __init__
        widget=Select2MultipleWidget(attrs={
            'class': 'form-control',
            'data-placeholder': 'Search and select team members...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': 0,
            'data-close-on-select': False,
        }),
        required=True,
        help_text='Select one or more users to add to this team'
    )
    class Meta:
        model = Team
        fields = ['name', 'team_lead', 'members', 'roles']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter team name',
                'autocomplete': 'off',
            }),
            'team_lead': Select2Widget(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select a team lead...',
                'data-allow-clear': 'false',
            }),
        }

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Store workspace for use in clean methods
        self.workspace = workspace

        # Ensure all fields are required
        self.fields['name'].required = True
        self.fields['team_lead'].required = True
        self.fields['members'].required = True
        self.fields['roles'].required = True

        # Custom error messages
        self.fields['name'].error_messages.update({
            'required': 'Team name is required.',
        })
        self.fields['team_lead'].error_messages.update({
            'required': 'Please select a team lead.',
        })
        self.fields['members'].error_messages.update({
            'required': 'Please select at least one team member.',
        })
        self.fields['roles'].error_messages.update({
            'required': 'Please select at least one role.',
        })

        # Filter users by workspace if provided
        if workspace:
            workspace_user_ids = Membership.objects.filter(
                workspace=workspace
            ).values_list('user_id', flat=True).distinct()

            users_qs = User.objects.filter(
                id__in=workspace_user_ids
            ).order_by('first_name', 'last_name', 'username')

            self.fields['team_lead'].queryset = users_qs
            self.fields['members'].queryset = users_qs
        else:
            all_users = User.objects.all().order_by('first_name', 'last_name', 'username')
            self.fields['team_lead'].queryset = all_users
            self.fields['members'].queryset = all_users

        # Custom user labels
        self.fields['team_lead'].label_from_instance = self._user_label
        self.fields['members'].label_from_instance = self._user_label

        # Handle Roles Initial Value (string representation of list to actual list)
        if self.instance.pk and self.instance.roles:
            try:
                import ast
                val = ast.literal_eval(self.instance.roles)
                if isinstance(val, list):
                    self.fields['roles'].initial = val
                else:
                    self.fields['roles'].initial = [val]
            except (ValueError, SyntaxError):
                self.fields['roles'].initial = [self.instance.roles]

    @staticmethod
    def _user_label(user):
        """Display user's full name or username"""
        full_name = user.get_full_name()
        return full_name if full_name.strip() else user.username

    def clean_name(self):
        """Validate that team name doesn't already exist within the workspace"""
        name = self.cleaned_data.get('name', '').strip()

        if not name:
            raise forms.ValidationError("Team name cannot be empty.")

        if self.workspace:
            query = Team.objects.filter(
                client__workspace=self.workspace,
                name__iexact=name
            )
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)

            if query.exists():
                raise forms.ValidationError(
                    f"A team named '{name}' already exists in this workspace."
                )

        return name

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        team_lead = cleaned_data.get('team_lead')
        members = cleaned_data.get('members')

        # Logic: Team lead must be part of the members list
        if team_lead and members:
            if team_lead not in members:
                raise forms.ValidationError(
                    "Team lead must be one of the selected team members."
                )

        return cleaned_data


class TeamEditForm(TeamForm):
    """Specific form for editing with prefilled values"""
    pass


# =========================
# TEAM MEMBERS FORM
# =========================

class TeamMembersForm(forms.Form):
    """
    Form for bulk member management.
    Filters available members based on selected action.
    """
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=Select2MultipleWidget(attrs={
            'class': 'form-control',
            'data-placeholder': 'Search and select members...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': 0,
            'data-close-on-select': False,
        }),
        required=True
    )

    action = forms.ChoiceField(
        choices=[
            ('add', 'Add Members'),
            ('replace', 'Replace All Members'),
            ('remove', 'Remove Members'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='add'
    )

    def __init__(self, *args, team=None, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = team
        self.workspace = workspace

        # 1. Base Queryset (Users in Workspace)
        if workspace:
            workspace_user_ids = Membership.objects.filter(
                workspace=workspace
            ).values_list('user_id', flat=True).distinct()
            qs = User.objects.filter(id__in=workspace_user_ids)
        else:
            qs = User.objects.all()

        # 2. Dynamic Filtering based on Action
        # We check self.data (POST) or default to 'add'
        action = (self.data.get('action') or 'add') if self.data else 'add'

        if team:
            if action == 'add':
                # SHOW ONLY NON-MEMBERS
                qs = qs.exclude(id__in=team.members.all())
            elif action == 'remove':
                # SHOW ONLY CURRENT MEMBERS
                qs = qs.filter(id__in=team.members.all())
            # For 'replace', we show all workspace users

        self.fields['members'].queryset = qs.order_by('first_name', 'last_name', 'username')
        self.fields['members'].label_from_instance = self._user_label

    @staticmethod
    def _user_label(user):
        full_name = user.get_full_name()
        return full_name if full_name.strip() else user.username

    def clean_members(self):
        members = self.cleaned_data.get('members')
        if not members:
            raise forms.ValidationError("Please select at least one member.")
        return members

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        members = cleaned_data.get('members')

        if action == 'remove' and self.team:
            # Prevent removing all members
            if len(members) >= self.team.members.count():
                raise forms.ValidationError("Cannot remove all members from a team.")

        return cleaned_data
