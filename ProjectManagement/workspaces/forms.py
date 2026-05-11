from django import forms


from workspaces.models import Workspace, Membership, Client


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

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'address', 'number', 'email', 'paid', 'amount_paid', 'paid_type', 'payment_date',
                  'total_amount', 'assigned_to']
