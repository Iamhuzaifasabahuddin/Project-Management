"""
Django Views for Team Management with Enhanced Forms

These views demonstrate how to integrate the new Team forms
(TeamForm, TeamEditForm, TeamMembersForm) into your application.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from Posts.models import Task
from Teams.models import Team
from workspaces.models import Client, Workspace
from workspaces.services import is_workspace_admin, is_workspace_member
from .forms import TeamForm, TeamMembersForm


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

    view_type = request.GET.get('view', 'card')

    context = {
        "client": client,
        "workspace": workspace,
        "teams": teams,
        "is_admin": is_admin,
        "view_type": view_type,
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

    form = TeamForm(request.POST or None, workspace=workspace, client=client)

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






@login_required
def all_user_teams(request):
    """
    List all teams for the logged-in user across all clients and workspaces.
    Workspace admins see all teams in their admin workspaces.
    """
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')

    # Check if user is a workspace admin of any workspace
    admin_workspaces = Workspace.objects.filter(membership__user=request.user, membership__role="admin")
    is_admin_of_any = admin_workspaces.exists()

    if request.user.is_superuser:
        teams_queryset = Team.objects.all().prefetch_related("members").annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        )
        is_admin = True
    elif is_admin_of_any:
        teams_queryset = Team.objects.filter(client__workspace__in=admin_workspaces).prefetch_related(
            "members").annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).distinct()
        is_admin = True
    else:
        teams_queryset = Team.objects.filter(
            Q(members=request.user) |
            Q(team_lead=request.user)
        ).distinct().prefetch_related("members").annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        )
        is_admin = False

    if search_query:
        teams_queryset = teams_queryset.filter(
            Q(name__icontains=search_query) |
            Q(client__name__icontains=search_query)
        )

    # Sorting
    if sort_by == 'name':
        teams_queryset = teams_queryset.order_by('name')
    elif sort_by == '-name':
        teams_queryset = teams_queryset.order_by('-name')
    elif sort_by == 'created':
        teams_queryset = teams_queryset.order_by('created_at')
    elif sort_by == '-created':
        teams_queryset = teams_queryset.order_by('-created_at')
    else:
        teams_queryset = teams_queryset.order_by('-id')

    view_type = request.GET.get('view', 'card')

    if request.headers.get('HX-Request'):
        return render(request, 'includes/team_list_fragment.html',
                      {'teams': teams_queryset, 'is_admin': is_admin, 'view_type': view_type})

    return render(request, 'teams/all_teams.html', {
        'teams': teams_queryset,
        'is_admin': is_admin,
        'search_query': search_query,
        'sort_by': sort_by,
        'view_type': view_type,
    })


# =========================
# TEAM DELETION VIEW
# =========================

@login_required
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
# ========================
