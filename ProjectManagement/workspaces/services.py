import datetime

from django.utils import timezone

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

def auto_archive_client_if_done(client):
    """
    Checks if all tasks for all teams of the client are completed.
    If so, sets is_archived to True.
    """
    from Posts.models import Task
    
    has_tasks = Task.objects.filter(team__client=client).exists()
    
    if not has_tasks:
        return False

    # Check if there are any tasks that are NOT completed
    has_pending = Task.objects.filter(
        team__client=client
    ).exclude(status='completed').exists()

    if not has_pending:
        client.is_archived = True
        client.archived_at = timezone.localdate()
        client.save()
        return True
        
    return False
