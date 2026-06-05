from workspaces.models import Membership

def is_workspace_admin(user, workspace):
    """Check if user is workspace admin or superuser"""
    if user.is_superuser:
        return True
    if not workspace:
        return False
    return Membership.objects.filter(
        user=user,
        workspace=workspace,
        role__iexact='admin'
    ).exists()

def is_workspace_member(user, workspace):
    """Check if user is workspace member or superuser"""
    if user.is_superuser:
        return True
    if not workspace:
        return False
    return Membership.objects.filter(
        user=user,
        workspace=workspace
    ).exists()
