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

def sync_client_teams(client):
    """
    Syncs team memberships for a client based on 'assigned_to' users
    and their roles in the workspace.
    """
    from Teams.models import Team
    from django.contrib.auth.models import User
    
    workspace = client.workspace
    workspace_admins = User.objects.filter(
        membership__workspace=workspace,
        membership__role="admin",
    )
    
    for team in client.teams.all():
        role_name = team.roles
        if not role_name:
            continue
            
        assigned_members = client.assigned_to.filter(
            membership__workspace=workspace,
            membership__role__in=[role_name, 'project manager']
        )
        
        # Ensure team lead is included
        if team.team_lead:
            team.members.add(team.team_lead)
            
        # Ensure admins are included
        if workspace_admins.exists():
            team.members.add(*workspace_admins)
            
        # Add assigned members based on role
        if assigned_members.exists():
            team.members.add(*assigned_members)
