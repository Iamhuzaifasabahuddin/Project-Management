import os


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from Posts.models import Post
from Teams.forms import TeamForm
from Teams.models import Team
from workspaces.forms import WorkspaceForm, RoleAssignForm, ClientForm
from workspaces.models import Workspace, Membership, Client
from workspaces.services import is_workspace_admin, is_workspace_member


# =========================
# DASHBOARD
# =========================
@login_required
def dashboard_view(request):
    from Posts.models import Task
    from django.db.models import Count, Q

    if request.user.is_superuser:
        workspaces = Workspace.objects.all()
        latest_teams = Team.objects.all().annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).order_by('-id')[:5]
        latest_tasks = Task.objects.filter(status="pending").order_by('-created_at')[:5]
        latest_clients = Client.objects.all().order_by('-id')[:5]
    else:
        workspaces = Workspace.objects.filter(membership__user=request.user)
        latest_teams = Team.objects.filter(members=request.user).annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).distinct().order_by('-id')[:5]
        latest_tasks = Task.objects.filter(assigned_to=request.user, status="pending").distinct().order_by(
            '-created_at')[:5]
        latest_clients = Client.objects.filter(teams__members=request.user, is_archived=False).distinct().order_by('-id')[:5]

    is_admin = request.user.is_superuser or Membership.objects.filter(
        user=request.user,
        role="admin"
    ).exists()

    context = {
        "workspaces": workspaces,
        "latest_teams": latest_teams,
        "latest_tasks": latest_tasks,
        "latest_clients": latest_clients,
        "is_admin": is_admin,
    }

    if request.headers.get('HX-Request'):
        return render(request, "includes/dashboard_workspace_list.html", context)

    return render(request, "dashboard.html", context)


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

    context = {
        "workspaces": workspaces,
        "memberships": Membership.objects.select_related("user", "workspace"),
        "is_admin": is_workspace_admin(request.user, None) or request.user.is_superuser,
    }

    if request.headers.get('HX-Request'):
        return render(request, "includes/workspace_list_fragment.html", context)

    return render(request, "workspace_list.html", context)


@login_required
def workspace_detail(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Superusers can access any workspace
    if not request.user.is_superuser:
        if not is_workspace_member(request.user, workspace):
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


@login_required
def all_clients(request):
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')
    filter_archived = request.GET.get('archived', 'active')

    if request.user.is_superuser:
        clients = Client.objects.all()
    else:
        # Non-superusers see clients they are part of through teams
        clients = Client.objects.filter(teams__members=request.user).distinct()

    # Filtering by archived status
    if filter_archived == 'active':
        clients = clients.filter(is_archived=False)
    elif filter_archived == 'archived':
        clients = clients.filter(is_archived=True)
    # if 'all', no filter applied

    if search_query:
        clients = clients.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query))

    # Sorting
    if sort_by == 'name':
        clients = clients.order_by('name')
    elif sort_by == '-name':
        clients = clients.order_by('-name')
    elif sort_by == 'created':
        clients = clients.order_by('created_at')
    elif sort_by == '-created':
        clients = clients.order_by('-created_at')
    else:
        clients = clients.order_by('-id')

    if request.headers.get('HX-Request'):
        return render(request, "includes/all_clients_list_fragment.html", {"clients": clients})

    return render(request, "all_clients.html", {
        "clients": clients,
        "is_admin": request.user.is_superuser or Membership.objects.filter(user=request.user, role="admin").exists(),
        "search_query": search_query,
        "sort_by": sort_by,
        "filter_archived": filter_archived,
    })

def get_users_by_role(workspace, role):
    return User.objects.filter(membership__workspace=workspace, membership__role=role)

def get_team_lead_by_email(email):
    """Get a user by email, returns None if not found"""
    if not email:
        return None
    try:
        return User.objects.get(email__iexact=email.strip())
    except User.DoesNotExist:
        return None

def add_user_to_workspace(user, workspace, role):
    """Add a user to workspace if not already a member. Returns the membership."""
    membership, created = Membership.objects.get_or_create(
        user=user,
        workspace=workspace,
        defaults={'role': role}
    )
    return membership, created

def create_default_teams_for_client(client, workspace):
    """
    Create default teams for a client with team leads from environment variables.

    Environment variables expected:
    - MARKETING_LEAD_EMAIL
    - DEVELOPER_LEAD_EMAIL
    - DESIGN_LEAD_EMAIL
    - EDITORIAL_LEAD_EMAIL
    - PUBLISHING_LEAD_EMAIL

    If team lead is not in workspace, they will be added.
    """
    TEAM_ROLES = [
        "marketing",
        "designer",
        "developer",
        "editor",
        "publisher",
    ]
    TEAM_NAMES = {
        "marketing": "Marketing",
        "designer": "Design",
        "developer": "Development",
        "editor": "Editorial",
        "publisher": "Publishing",
    }
    lead_email_env_map = {
        "marketing": "MARKETING_LEAD_EMAIL",
        "designer": "DESIGN_LEAD_EMAIL",
        "developer": "DEVELOPER_LEAD_EMAIL",
        "editor": "EDITORIAL_LEAD_EMAIL",
        "publisher": "PUBLISHING_LEAD_EMAIL",
    }

    for role_name in TEAM_ROLES:
        lead_email = os.getenv(lead_email_env_map.get(role_name))
        team_lead = None

        if lead_email:
            team_lead = get_team_lead_by_email(lead_email)
            if team_lead:
                add_user_to_workspace(team_lead, workspace, role=role_name)
            else:
                print(f"Warning: Team lead with email {lead_email} for {role_name} not found")

        team = Team.objects.create(
    client=client,
            name=f"{TEAM_NAMES.get(role_name)} Team",
            roles=role_name,
            team_lead=team_lead
        )

        if team_lead:
            team.members.add(team_lead)


@login_required
def create_clients(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    if not request.user.is_superuser or is_workspace_admin(request.user, workspace):
        if not is_workspace_member(request.user, workspace):
            raise PermissionDenied("Not a member of this workspace")

    form = ClientForm(request.POST or None)

    if form.is_valid():
        client = form.save(commit=False)
        client.workspace = workspace
        client.save()
        # form.save_m2m()
        create_default_teams_for_client(client, workspace)
        return redirect("client_details", workspace_id=workspace.id)

    return render(request, "create_client.html", {
        "form": form,
        "workspace": workspace,
        "is_admin": is_workspace_admin(request.user, workspace),
    })


@login_required
def client_list(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Superusers see all clients in workspace
    if request.user.is_superuser:
        all_clients = Client.objects.filter(workspace=workspace)
    else:
        # Get clients linked to teams the user is a member of in this workspace
        all_clients = Client.objects.filter(
            workspace=workspace,
            teams__members=request.user
        ).distinct()

    active_clients = all_clients.filter(is_archived=False)
    archived_clients = all_clients.filter(is_archived=True)

    return render(request, "client_list.html", {
        "active_clients": active_clients,
        "archived_clients": archived_clients,
        "workspace": workspace,
    })


@login_required
def client_detail(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    # Superusers can access any workspace
    if not request.user.is_superuser or not is_workspace_admin(request.user, workspace):
        if not is_workspace_member(request.user, workspace):
            raise PermissionDenied("Not a member")

    # Superusers see all clients in workspace
    if request.user.is_superuser or is_workspace_admin(request.user, workspace):
        all_clients = Client.objects.filter(workspace=workspace)
    else:
        all_clients = Client.objects.filter(
            workspace=workspace,
            teams__members=request.user
        ).distinct()

    active_clients = all_clients.filter(is_archived=False)
    archived_clients = all_clients.filter(is_archived=True)

    context = {
        "workspace": workspace,
        "active_clients": active_clients,
        "archived_clients": archived_clients,
        "is_admin": is_workspace_admin(request.user, workspace),
        "is_member": is_workspace_member(request.user, workspace),
    }

    if request.headers.get('HX-Request'):
        return render(request, "includes/client_list_fragment.html", context)

    return render(request, "client_details.html", context)


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
