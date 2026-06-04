from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from Posts.models import Post
from Teams.forms import TeamForm
from Teams.models import Team
from Teams.views import is_workspace_admin
from workspaces.forms import WorkspaceForm, RoleAssignForm, ClientForm
from workspaces.models import Workspace, Membership, Client


# =========================
# HELPER
# =========================
def role_checker(user, workspace, role):
    """Check if user has a specific role, or is superuser"""
    if user.is_superuser:
        return True
    if workspace is None:
        return Membership.objects.filter(user=user, role=role).exists()
    return Membership.objects.filter(user=user, workspace=workspace, role=role).exists()

def get_users_by_role(workspace, role):
    return User.objects.filter(membership__workspace=workspace, membership__role=role)

def create_default_teams_for_client(client, workspace):
    TEAM_ROLES = [
        "marketing",
        "designer",
        "developer",
        "publisher",
    ]

    for role_name in TEAM_ROLES:

        membership = Membership.objects.filter(
            role__iexact=role_name,
            workspace=workspace
        ).first()

        if not membership:
            continue

        team = Team.objects.create(
            client=client,
            name=f"{role_name.title()} Team",
            roles=role_name
        )

        users = get_users_by_role(workspace, role_name)
        team.members.set(users)

# =========================
# DASHBOARD
# =========================

@login_required
def dashboard_view(request):

    if request.user.is_superuser:
        workspaces = Workspace.objects.all()
    else:
        workspaces = Workspace.objects.filter(membership__user=request.user)

    is_admin = request.user.is_superuser or Membership.objects.filter(
        user=request.user,
        role="admin"
    ).exists()

    return render(request, "dashboard.html", {
        "workspaces": workspaces,
        "is_admin": is_admin,
    })


# =========================
# WORKSPACE MANAGEMENT
# =========================

@login_required
def create_workspace(request):
    is_admin = request.user.is_superuser or Membership.objects.filter(
        user=request.user,
        role="admin",
    ).exists()

    if not is_admin:
        raise PermissionDenied("Not allowed")

    form = WorkspaceForm(request.POST or None)

    if form.is_valid():
        workspace = form.save(commit=False)
        workspace.owner = request.user
        workspace.save()

        Membership.objects.create(
            user=request.user,
            workspace=workspace,
            role="admin",
        )

        messages.success(request, "Workspace created")
        return redirect("dashboard")

    return render(request, "create_workspace.html", {"form": form})


@login_required
def workspace_list(request):
    # Superusers see all workspaces
    if request.user.is_superuser:
        workspaces = Workspace.objects.all()
    else:
        workspaces = Workspace.objects.filter(membership__user=request.user)

    return render(request, "workspace_list.html", {
        "workspaces": workspaces,
        "memberships": Membership.objects.select_related("user", "workspace"),
        "is_admin": role_checker(request.user, None, "admin") or request.user.is_superuser,
    })


@login_required
def workspace_detail(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Superusers can access any workspace
    if not request.user.is_superuser:
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not a member")

    posts = Post.objects.filter(client__workspace=workspace).order_by("-created_at")

    return render(request, "workspace_detail.html", {
        "workspace": workspace,
        "posts": posts,
    })


from django.db import transaction

# =========================
# ROLE ASSIGNMENT
# =========================

@login_required
def assign_role(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only superuser allowed")

    form = RoleAssignForm(request.POST or None)

    if form.is_valid():
        users = form.cleaned_data['users']
        workspace = form.cleaned_data['workspace']
        role = form.cleaned_data['role']
        
        with transaction.atomic():
            memberships = [
                Membership(user=user, workspace=workspace, role=role)
                for user in users
            ]
            Membership.objects.bulk_create(memberships)
            
        messages.success(request, f"Successfully assigned '{role}' role to {len(users)} users.")
        return redirect("workspace_list")

    return render(request, "assign_role.html", {"form": form})


# =========================
# CLIENTS
# =========================

@login_required
def create_clients(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Superusers can create clients in any workspace
    if not request.user.is_superuser:
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not a member of this workspace")

    form = ClientForm(request.POST or None)

    if form.is_valid():
        client = form.save(commit=False)
        client.workspace = workspace
        client.save()
        form.save_m2m()
        # create_default_teams_for_client(client, workspace)
        return redirect("client_details", workspace_id=workspace.id)

    return render(request, "create_client.html", {
        "form": form,
        "workspace": workspace,
        "is_admin": role_checker(request.user, workspace, "admin"),
    })


@login_required
def client_list(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Superusers see all clients in workspace
    if request.user.is_superuser:
        clients = Client.objects.filter(workspace=workspace)
    else:
        clients = Client.objects.filter(workspace=workspace, assigned_to=request.user)

    return render(request, "client_list.html", {
        "clients": clients,
        "workspace": workspace,
    })


@login_required
def client_detail(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Superusers can access any workspace
    if not request.user.is_superuser:
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not a member")

    # Superusers see all clients in workspace
    if request.user.is_superuser:
        clients = Client.objects.filter(workspace=workspace)
    else:
        clients = Client.objects.filter(
            workspace=workspace,
            teams__members=request.user
        ).distinct()

    return render(request, "client_details.html", {
        "workspace": workspace,
        "clients": clients,
        "is_admin": role_checker(request.user, workspace, "admin"),
        "is_member": role_checker(request.user, workspace, "member") or request.user.is_superuser,
    })

@login_required
def view_client_details(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    # Superusers can view any client
    if not request.user.is_superuser:
        workspace = client.workspace
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not a member of this workspace")

    return render(request, "view_client_details.html", {
        "client": client,
    })

@login_required
def client_posts(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    # Superusers can view any client's posts
    if not request.user.is_superuser:
        workspace = client.workspace
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not a member of this workspace")

    return render(request, "task_posts.html", {
        "client": client,
        "posts": client.posts.all().order_by("-created_at"),
    })

@login_required
def team_posts(request, team_id):

    team = get_object_or_404(Team, id=team_id)

    workspace = team.client.workspace

    # 🔐 workspace membership check
    if not Membership.objects.filter(
        user=request.user,
        workspace=workspace
    ).exists():
        raise PermissionDenied("Not a member")

    # ✅ admin check
    is_admin = Membership.objects.filter(
        user=request.user,
        workspace=workspace,
        role__iexact="admin"
    ).exists()

    # 🔐 only team members OR admins can access
    if not is_admin and request.user not in team.members.all():
        raise PermissionDenied("Not part of this team")

    posts = team.posts.select_related(
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

        is_workspace_member = Membership.objects.filter(
            user=request.user,
            workspace=workspace
        ).exists()

        if not is_workspace_member:
            raise PermissionDenied("Not a member")

    # =========================================
    # ADMIN CHECK
    # =========================================
    is_admin = (
        request.user.is_superuser
        or
        Membership.objects.filter(
            user=request.user,
            workspace=workspace,
            role__iexact="admin"
        ).exists()
    )

    # =========================================
    # TEAM QUERYSET
    # =========================================

    # 🔥 Admins see ALL teams
    if is_admin:

        teams = client.teams.prefetch_related(
            "members"
        ).order_by("roles", "name")

    # 🔥 Normal users see ONLY their teams
    else:

        teams = client.teams.filter(
            members=request.user
        ).prefetch_related(
            "members"
        ).distinct().order_by("roles", "name")

    # =========================================
    # RENDER
    # =========================================
    return render(request, "client_teams.html", {
        "client": client,
        "workspace": workspace,
        "teams": teams,
        "is_admin": is_admin,
    })


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
