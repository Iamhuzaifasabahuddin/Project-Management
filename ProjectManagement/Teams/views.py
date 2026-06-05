"""
Django Views for Team Management with Enhanced Forms

These views demonstrate how to integrate the new Team forms
(TeamForm, TeamEditForm, TeamMembersForm) into your application.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction, models
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods

from Posts.models import Task
from workspaces.services import is_workspace_admin, is_workspace_member
from Teams.models import Team
from workspaces.models import Client, Membership
from .forms import TeamForm, TeamEditForm, TeamMembersForm

@login_required
def team_posts(request, task_id):

    task = get_object_or_404(Task, id=task_id)

    workspace = task.team.client.workspace
    client = task.team.client
    team = task.team

    # =========================================
    # SUPERUSER BYPASS
    # =========================================
    if request.user.is_superuser:
        is_admin = True

    else:

        # =========================================
        # WORKSPACE MEMBERSHIP CHECK
        # =========================================
        if not is_workspace_member(request.user, workspace) and not is_team_member(request.user, team):
            raise PermissionDenied("Not a member")

        # =========================================
        # ADMIN CHECK
        # =========================================
        is_admin = is_workspace_admin(request.user, workspace)

        # =========================================
        # TEAM ACCESS CHECK
        # =========================================
        if not is_admin and request.user not in team.members.all():
            raise PermissionDenied("Not part of this team")

    # =========================================
    # POSTS QUERY
    # =========================================
    posts = task.posts.select_related(
        "author"
    ).prefetch_related(
        "files",
        "comments"
    ).order_by("-created_at")

    return render(request, "task_posts.html", {
        "team": team,
        "client": team.client,
        "workspace": workspace,
        "posts": posts,
        "is_admin": is_admin,
    })

@login_required
def client_teams(request, client_id):

    client = get_object_or_404(Client, id=client_id)
    workspace = client.workspace

    # =========================================
    # WORKSPACE ACCESS CHECK
    # =========================================
    if not request.user.is_superuser:

        member = is_workspace_member(request.user, workspace)

        if not member:
            raise PermissionDenied("Not a member")

    # =========================================
    # ADMIN CHECK
    # =========================================
    is_admin = (
        request.user.is_superuser
        or
        is_workspace_admin(request.user, workspace)
    )

    # =========================================
    # TEAM QUERYSET
    # =========================================

    if is_admin:

        teams = client.teams.prefetch_related(
            "members"
        ).annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).order_by("roles", "name")

    else:

        teams = client.teams.filter(
            members=request.user
        ).prefetch_related(
            "members"
        ).annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).distinct().order_by("roles", "name")

    tasks = teams
    context = {
        "client": client,
        "workspace": workspace,
        "teams": teams,
        "is_admin": is_admin,
    }

    if request.headers.get('HX-Request'):
        return render(request, "includes/team_list_fragment.html", context)

    return render(request, "client_teams.html", context)


def can_manage_team(user, team):
    """
    Check if user can manage this team (Add/Remove members).
    Allowed for: Superusers, Workspace Admins, and the Team Lead.
    """
    if user.is_superuser:
        return True
    
    workspace = team.client.workspace
    is_admin = is_workspace_admin(user, workspace)
    
    is_lead = team.team_lead == user
    
    return is_admin or is_lead


def is_team_member(user, team):
    """Check if user is a team member"""
    return team.members.filter(id=user.id).exists()


# =========================
# TEAM CREATION VIEWS
# =========================

@login_required
def create_team(request, client_id):
    """
    Create a new team for a client.

    Permissions:
    - Workspace admin only
    - Superusers allowed
    """
    client = get_object_or_404(Client, id=client_id)
    workspace = client.workspace

    # Permission check
    if not is_workspace_admin(request.user, workspace):
        raise PermissionDenied("Only workspace admins can create teams")

    form = TeamForm(request.POST or None, workspace=workspace)

    if form.is_valid():
            team = form.save(commit=False)
            team.client = client
            team.save()
            form.save_m2m()

            messages.success(
                request,
                f"Team '{team.name}' created successfully with {team.members.count()} members"
            )
            return redirect('client_teams', client_id=client.id)

    return render(request, 'teams/create_team.html', {
        'form': form,
        'client': client,
        'workspace': workspace,
    })


# =========================
# TEAM MEMBER MANAGEMENT VIEWS
# =========================

@login_required
def manage_team_members(request, team_id):
    """
    Quick member management with bulk actions (Add/Replace/Remove).

    Permissions:
    - Workspace admin
    - Team Lead
    - Superusers
    """
    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace
    client = team.client

    # Permission check: Workspace Admin, Superuser, OR Team Lead
    if not can_manage_team(request.user, team):
        raise PermissionDenied("You don't have permission to manage this team's members")

    action = request.GET.get('action', 'add')
    form = TeamMembersForm(
        request.POST or None,
        team=team,
        workspace=workspace,
        initial={'action': action}
    )

    if form.is_valid():
        with transaction.atomic():
            members = form.cleaned_data['members']
            action = form.cleaned_data['action']

            if action == 'add':
                team.members.add(*members)
                member_names = ', '.join([str(m) for m in members])
                messages.success(
                    request,
                    f"Added {len(members)} member(s) to '{team.name}': {member_names}"
                )

            elif action == 'replace':
                old_count = team.members.count()
                team.members.set(members)
                messages.success(
                    request,
                    f"Team '{team.name}' now has {len(members)} members (was {old_count})"
                )

            elif action == 'remove':
                member_names = ', '.join([str(m) for m in members])
                team.members.remove(*members)
                messages.success(
                    request,
                    f"Removed {len(members)} member(s) from '{team.name}': {member_names}"
                )

            return redirect('client_teams', client_id=team.client.id)

    return render(request, "teams/manage_team_members.html", {
        'form': form,
        'team': team,
        'current_members': team.members.all(),
        'workspace': workspace,
        'client': client,
    })


# =========================
# TEAM DETAIL/LIST VIEWS
# =========================

@login_required
@require_http_methods(["GET"])
def team_detail(request, team_id):
    """
    Display team details including members and info.

    Permissions:
    - Team members
    - Workspace admins
    - Team Lead
    - Superusers
    """
    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace

    # Permission check
    is_member = is_team_member(request.user, team)
    is_admin = is_workspace_admin(request.user, workspace)
    is_lead = (team.team_lead == request.user)

    if not (is_member or is_admin or is_lead):
        raise PermissionDenied("You don't have access to this team")

    return render(request, 'teams/team_detail.html', {
        'team': team,
        'workspace': workspace,
        'members': team.members.all().order_by('first_name', 'last_name'),
        'is_admin': is_admin,
        'is_lead': is_lead,
        'can_edit': is_admin or is_lead,
    })


@login_required
def team_list(request, client_id):
    """
    List all teams for a client.

    Permissions:
    - Workspace members
    - Superusers
    """
    client = get_object_or_404(Client, id=client_id)
    workspace = client.workspace
    is_admin = is_workspace_admin(request.user, workspace)

    # Permission check
    if not request.user.is_superuser or not is_admin:
        if not is_workspace_member(request.user, workspace):
            raise PermissionDenied("Not a member of this workspace")


    if request.user.is_superuser or is_admin:
        teams = Team.objects.filter(client=client)
    else:
        teams = Team.objects.filter(
            client=client,
            members=request.user
        ) | Team.objects.filter(
            client=client,
            team_lead=request.user
        ) | Team.objects.filter(
            client=client,
            client__workspace__membership__user=request.user,
            client__workspace__membership__role__iexact='admin'
        )
        teams = teams.distinct()


    return render(request, 'teams/team_list.html', {
        'teams': teams,
        'client': client,
        'workspace': workspace,
        'is_admin': is_admin,
    })


# =========================
# TEAM DELETION VIEW
# =========================

@login_required
@require_http_methods(["POST"])
def delete_team(request, team_id):
    """
    Delete a team (soft delete recommended).

    Permissions:
    - Workspace admin only
    - Superusers
    """
    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace
    client = team.client

    # Permission check
    if not is_workspace_admin(request.user, workspace) or not request.user.is_superuser:
        raise PermissionDenied("Only workspace admins can delete teams")

    team_name = team.name
    team.delete()

    messages.success(request, f"Team '{team_name}' deleted successfully")
    return redirect('client_teams', client_id=client.id)


# =========================
# TEAM MEMBER QUICK ACTIONS
# =========================

@login_required
@require_http_methods(["POST"])
def add_user_to_team(request, team_id, user_id):
    """
    Quick action to add a single user to a team.

    Permissions:
    - Workspace admin
    - Team Lead
    - Superusers
    """
    team = get_object_or_404(Team, id=team_id)
    user = get_object_or_404(User, id=user_id)
    
    # Permission check
    if not can_manage_team(request.user, team):
        raise PermissionDenied("You don't have permission to add members to this team")

    # Verify user is in workspace
    if not request.user.is_superuser:
        if not Membership.objects.filter(
                user=user,
                workspace=team.client.workspace
        ).exists():
            raise PermissionDenied("User is not a member of this workspace")

    team.members.add(user)
    messages.success(request, f"{user} added to '{team.name}'")

    return redirect('client_teams', client_id=team.client.id)


@login_required
@require_http_methods(["POST"])
def remove_user_from_team(request, team_id, user_id):
    """
    Quick action to remove a user from a team.

    Permissions:
    - Workspace admin
    - Team Lead
    - Superusers
    - User removing themselves
    """
    team = get_object_or_404(Team, id=team_id)
    user = get_object_or_404(User, id=user_id)

    is_manager = can_manage_team(request.user, team)
    is_self = request.user.id == user.id

    # Permission check
    if not (is_manager or is_self):
        raise PermissionDenied("You don't have permission to remove members")

    # Prevent removing last member
    if team.members.count() <= 1:
        messages.error(request, "Cannot remove the last member from a team")
        return redirect('client_teams', client_id=team.client.id)

    team.members.remove(user)

    if is_self:
        messages.success(request, f"You've been removed from '{team.name}'")
    else:
        messages.success(request, f"{user} removed from '{team.name}'")

    return redirect('client_teams', client_id=team.client.id)


# =========================
# TEAM STATISTICS VIEW
# =========================

@login_required
@require_http_methods(["GET"])
def team_statistics(request, team_id):
    """
    Display team statistics and member information.

    Permissions:
    - Team members
    - Workspace admins
    - Team Lead
    - Superusers
    """
    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace

    # Permission check
    is_member = is_team_member(request.user, team)
    is_admin = is_workspace_admin(request.user, workspace)
    is_lead = (team.team_lead == request.user)

    if not (is_member or is_admin or is_lead):
        raise PermissionDenied("You don't have access to this team")

    members = team.members.all()

    stats = {
        'total_members': members.count(),
        'members_with_posts': members.filter(
            posts__team=team
        ).distinct().count(),
        'members_with_comments': members.filter(
            comment__post__team=team
        ).distinct().count(),
    }

    return render(request, 'teams/team_statistics.html', {
        'team': team,
        'workspace': workspace,
        'members': members,
        'stats': stats,
        'is_admin': is_admin,
    })
