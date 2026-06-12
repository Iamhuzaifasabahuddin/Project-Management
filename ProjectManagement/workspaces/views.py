import os

from django.urls import reverse
from dotenv import load_dotenv

load_dotenv(".env")

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from Posts.models import Post
from Teams.forms import TeamForm
from Teams.models import Team
from workspaces.forms import WorkspaceForm, RoleAssignForm, ClientForm
from workspaces.models import Workspace, Membership, Client
from workspaces.services import is_workspace_admin, is_workspace_member, sync_client_teams
from Posts.tasks import send_client_assigned_notification_task

# =========================
# LANDING PAGE
# =========================

def landing_page(request):
    """
    Public landing page for unauthenticated users.
    Redirects to dashboard if user is already logged in.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html")


# =========================
# ADMIN HUB (STATISTICS)
# =========================

from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta


@login_required
def admin_hub(request):
    """
    Centralized hub for administrative statistics across the entire application.
    Restricted to superusers and workspace admins.
    """
    # Permission Check
    is_admin = request.user.is_superuser or Membership.objects.filter(
        user=request.user,
        role="admin"
    ).exists()

    if not is_admin:
        raise PermissionDenied("You do not have permission to view the Admin Hub.")

    from Posts.models import Task, Post, Comment

    # User Stats
    total_users = User.objects.count()
    active_users_last_30 = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count()

    # Workspace & Team Stats
    total_workspaces = Workspace.objects.count()
    total_teams = Team.objects.count()

    # Client Stats
    clients_qs = Client.objects.all()
    total_clients = clients_qs.count()
    active_clients = clients_qs.filter(is_archived=False).count()
    archived_clients = clients_qs.filter(is_archived=True).count()

    # Financial Stats
    financials = clients_qs.aggregate(
        total_revenue=Sum('amount_paid'),
        total_contract_value=Sum('total_amount')
    )
    total_revenue = financials['total_revenue'] or 0
    total_contract_value = financials['total_contract_value'] or 0
    total_outstanding = total_contract_value - total_revenue

    # Task Stats
    tasks_qs = Task.objects.all()
    total_tasks = tasks_qs.count()
    task_stats = tasks_qs.aggregate(
        pending=Count('id', filter=Q(status='pending')),
        awaiting_approval=Count('id', filter=Q(status='awaiting_approval')),
        completed=Count('id', filter=Q(status='completed'))
    )

    overdue_tasks = tasks_qs.filter(
        due_date__lt=timezone.localdate()
    ).exclude(status='completed').count()

    # Engagement Stats
    total_posts = Post.objects.count()
    total_comments = Comment.objects.count()

    context = {
        "stats": {
            "users": {
                "total": total_users,
                "active_30d": active_users_last_30,
            },
            "workspaces": {
                "total": total_workspaces,
            },
            "teams": {
                "total": total_teams,
            },
            "clients": {
                "total": total_clients,
                "active": active_clients,
                "archived": archived_clients,
            },
            "financials": {
                "revenue": total_revenue,
                "contract_value": total_contract_value,
                "outstanding": total_outstanding,
            },
            "tasks": {
                "total": total_tasks,
                "pending": task_stats['pending'],
                "awaiting_approval": task_stats['awaiting_approval'],
                "completed": task_stats['completed'],
                "overdue": overdue_tasks,
            },
            "engagement": {
                "posts": total_posts,
                "comments": total_comments,
            }
        },
        "is_admin": True,
    }

    return render(request, "admin_hub.html", context)


# =========================
# DASHBOARD
# =========================
@login_required
def dashboard_view(request):
    from Posts.models import Task
    from django.db.models import Count, Q

    # Get workspaces where user is admin
    admin_workspaces = Workspace.objects.filter(membership__user=request.user, membership__role="admin")

    member_workspaces = Workspace.objects.filter(membership__user=request.user)

    if request.user.is_superuser:
        workspaces = Workspace.objects.all()
        latest_teams = Team.objects.all().select_related('client', 'team_lead').prefetch_related('members').annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).distinct().order_by('-id')[:5]
        latest_tasks = Task.objects.filter(status="pending").select_related('team').order_by('-created_at')[:5]
        latest_clients = Client.objects.all().order_by('-id')[:5]
        is_admin = True
    elif admin_workspaces.exists():
        workspaces = member_workspaces
        latest_teams = Team.objects.filter(client__workspace__in=admin_workspaces).select_related('client',
                                                                                                  'team_lead').prefetch_related(
            'members').annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).distinct().order_by('-id')[:5]

        latest_tasks = Task.objects.filter(team__client__workspace__in=admin_workspaces,
                                           status="pending").select_related('team').order_by('-created_at')[:5]
        latest_clients = Client.objects.filter(workspace__in=admin_workspaces).order_by('-id')[:5]
        is_admin = True
    else:
        # Regular user sees only their own
        workspaces = member_workspaces
        latest_teams = Team.objects.filter(members=request.user).select_related('client', 'team_lead').prefetch_related(
            'members').annotate(
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).distinct().order_by('-id')[:5]
        latest_tasks = Task.objects.filter(assigned_to=request.user, status="pending").select_related(
            'team').distinct().order_by(
            '-created_at')[:5]
        latest_clients = Client.objects.filter(teams__members=request.user, is_archived=False).distinct().order_by(
            '-id')[:5]
        is_admin = False

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


import csv
from django.http import HttpResponse


@login_required
def export_archived_clients(request):
    if not request.user.is_superuser and not Membership.objects.filter(user=request.user, role="admin").exists():
        raise PermissionDenied("Only admins can export clients")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="archived_clients.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Address', 'Number', 'Archived At'])

    clients = Client.objects.filter(is_archived=True)
    if not request.user.is_superuser:
        clients = clients.filter(workspace__membership__user=request.user,
                                 workspace__membership__role='admin').distinct()

    for client in clients:
        writer.writerow([client.id, client.name, client.email, client.address, client.number, client.archived_at])

    return response


@login_required
def all_clients(request):
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')
    filter_archived = request.GET.get('archived', 'active')
    view_type = request.GET.get('view', 'card')

    is_admin = request.user.is_superuser or Membership.objects.filter(
        user=request.user,
        role="admin"
    ).exists()

    if request.user.is_superuser:
        clients = Client.objects.all()
    elif is_admin:
        workspaces = Workspace.objects.filter(membership__user=request.user, membership__role="admin")
        clients = Client.objects.filter(workspace__in=workspaces).distinct()
    else:
        clients = Client.objects.filter(teams__members=request.user).distinct()

    if filter_archived == 'active':
        clients = clients.filter(is_archived=False)
    elif filter_archived == 'archived':
        clients = clients.filter(is_archived=True)

    if search_query:
        clients = clients.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query))

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

    context = {
        "clients": clients,
        "is_admin": is_admin,
        "search_query": search_query,
        "sort_by": sort_by,
        "filter_archived": filter_archived,
        "view_type": view_type,
    }

    if request.headers.get('HX-Request'):
        return render(request, "includes/all_clients_list_fragment.html", context)

    return render(request, "all_clients.html", context)


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

    workspace_admins = User.objects.filter(
        membership__workspace=workspace,
        membership__role="admin",
    )
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
        assigned_members = client.assigned_to.filter(
            membership__workspace=workspace,
            membership__role__in=[role_name, 'project manager']
        )
        if workspace_admins.exists():
            team.members.add(*workspace_admins)
        if assigned_members.exists():
            team.members.add(*assigned_members)


@login_required
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    workspace = client.workspace
    

    if not request.user.is_superuser and not is_workspace_admin(request.user, workspace):
        raise PermissionDenied("Only workspace admins can edit clients")

    form = ClientForm(request.POST or None, instance=client, workspace=workspace)

    if form.is_valid():
        client = form.save(commit=False)
        form.save_m2m()
        sync_client_teams(client)
        messages.success(request, f"Client '{client.name}' updated successfully.")
        return redirect("view_client", client_id=client.id)

    return render(request, "edit_client.html", {
        "form": form,
        "client": client,
        "workspace": workspace,
    })


@login_required
def create_clients(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    if not request.user.is_superuser or is_workspace_admin(request.user, workspace):
        if not is_workspace_member(request.user, workspace):
            raise PermissionDenied("Not a member of this workspace")

    form = ClientForm(request.POST or None, workspace=workspace)

    if form.is_valid():
        client = form.save(commit=False)
        client.workspace = workspace
        client.save()
        form.save_m2m()
        create_default_teams_for_client(client, workspace)

        client_url = request.build_absolute_uri(
            reverse('client_details', kwargs={'workspace_id': workspace.id})
        )
        to_emails = [user.email for user in client.assigned_to.all() if user.email]
        send_client_assigned_notification_task.delay(
                user_id=request.user.id,
                client_id=client.id,
                to_email=to_emails,
            url=client_url
            )
            
        messages.success(request, f"Client '{client.name}' created successfully.")
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
        "is_admin": is_workspace_admin(request.user, client.workspace) or request.user.is_superuser,
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
