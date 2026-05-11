from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from Posts.models import Post
from workspaces.forms import WorkspaceForm, RoleAssignForm, ClientForm
from workspaces.models import Workspace, Membership, Client


# Create your views here.

# =========================
# DASHBOARD
# =========================

@login_required
def dashboard_view(request):
    workspaces = Workspace.objects.filter(membership__user=request.user)

    is_admin = Membership.objects.filter(
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
        return redirect("workspace_list")

    return render(request, "create_workspace.html", {"form": form})


@login_required
def workspace_list(request):
    return render(request, "workspace_list.html", {
        "workspaces": Workspace.objects.all(),
        "memberships": Membership.objects.select_related("user", "workspace"),
        "is_admin": request.user.is_superuser or Membership.objects.filter(
            user=request.user, role="admin"
        ).exists(),
    })


@login_required
def workspace_detail(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
        raise PermissionDenied("Not a member")

    posts = Post.objects.filter(client__workspace=workspace).order_by("-created_at")

    return render(request, "workspace_detail.html", {
        "workspace": workspace,
        "posts": posts,
    })


# =========================
# ROLE ASSIGNMENT
# =========================

@login_required
def assign_role(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only superuser allowed")

    form = RoleAssignForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect("workspace_list")

    return render(request, "assign_role.html", {"form": form})


# =========================
# CLIENTS
# =========================

@login_required
def create_clients(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    form = ClientForm(request.POST or None)

    if form.is_valid():
        client = form.save(commit=False)
        client.workspace = workspace
        client.save()
        return redirect("client_details", workspace_id=workspace.id)

    return render(request, "create_client.html", {
        "form": form,
        "workspace": workspace,
    })


@login_required
def client_list(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    return render(request, "client_list.html", {
        "clients": Client.objects.filter(workspace=workspace),
        "workspace": workspace,
    })


@login_required
def client_detail(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
        raise PermissionDenied("Not a member")

    return render(request, "client_details.html", {
        "workspace": workspace,
        "clients": Client.objects.filter(workspace=workspace),
    })


@login_required
def client_posts(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    return render(request, "client_posts.html", {
        "client": client,
        "posts": client.posts.all().order_by("-created_at"),
    })
