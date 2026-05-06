# accounts/views.py
import pprint

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .forms import RegisterForm, WorkspaceForm, RoleAssignForm, PostForm, CommentForm
from .models import Workspace, Membership, Post, Comment


def register_view(request):
    """
    Handle user registration.

    Creates a new user using RegisterForm.
    On successful registration, logs the user in and redirects to dashboard.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            login(request, user)
            messages.success(request, f"Account created successfully! Welcome {user.first_name}!")
            return redirect('dashboard')

        return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Authenticate and log in a user.

    Validates username and password.
    On success, redirects to dashboard.
    On failure, returns login page with error message.
    """
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            print("User logged in")
            return redirect('dashboard')
        else:
            error = "Invalid username or password."
    return render(request, 'accounts/login.html', {'error': error})


@login_required
def dashboard_view(request):
    """
    Handle user dashboard.
    """
    workspaces = Workspace.objects.filter(membership__user=request.user)

    memberships = Membership.objects.filter(user=request.user)


    is_admin = memberships.filter(role="admin").exists()

    context = {
        "workspaces": workspaces,
        "is_admin": is_admin,
    }

    return render(request, "accounts/dashboard.html", context)

def logout_view(request):
    """
    Log out the current user and redirect to login page.
    """
    logout(request)
    return redirect('login')


@login_required
def create_workspace(request):
    """
    Create a new workspace or sub-workspace.

    Superusers can create main workspaces.
    Admins can create sub-workspaces under workspaces they administer.
    """

    is_admin = request.user.is_superuser or Membership.objects.filter(
        user=request.user,
        role='admin'
    ).exists()

    if not is_admin:
        raise PermissionDenied(
            "Only superusers and workspace admins can create workspaces"
        )

    form = WorkspaceForm(request.POST or None)

    # Limit parent selection to only root workspaces
    form.fields['parent'].queryset = Workspace.objects.filter(parent__isnull=True)

    if form.is_valid():
        parent = form.cleaned_data.get('parent')

        # 🔐 Permission check for sub-workspace creation
        if parent:
            has_admin_rights = Membership.objects.filter(
                user=request.user,
                workspace=parent,
                role='admin'
            ).exists()

            if not has_admin_rights and not request.user.is_superuser:
                raise PermissionDenied(
                    "Only admins of parent workspace or superuser can create sub-workspaces"
                )
        else:
            if not request.user.is_superuser:
                raise PermissionDenied(
                    "Only superuser can create main workspaces"
                )

        # ✅ Create workspace
        workspace = form.save(commit=False)
        workspace.owner = request.user
        workspace.save()

        # 🔥 Automatically assign creator as admin of this workspace
        Membership.objects.create(
            user=request.user,
            workspace=workspace,
            role='admin'
        )

        messages.success(
            request,
            f"Workspace '{workspace.name}' created successfully!"
        )
        return redirect('workspace_list')

    return render(request, 'accounts/create_workspace.html', {
        'form': form
    })

@login_required
def assign_role(request):
    """
    Assign a role to a user within a workspace (superuser only).

    Uses RoleAssignForm to create/update Membership records.
    """
    if not request.user.is_superuser:
        raise PermissionDenied("Only superuser can assign roles")

    form = RoleAssignForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('workspace_list')

    return render(request, 'accounts/assign_role.html', {'form': form})


@login_required
def workspace_list(request):
    """
    Display all workspaces and their memberships.

    Superusers see all workspaces and membership mappings.
    """
    workspaces = Workspace.objects.filter(parent__isnull=True)

    memberships = Membership.objects.select_related('user', 'workspace')

    return render(request, 'accounts/workspace_list.html', {
        'workspaces': workspaces,
        'memberships': memberships
    })



@login_required
def workspace_detail(request, workspace_id):
    """
    Display details of a workspace, including its posts.
    """
    workspace = get_object_or_404(Workspace, id=workspace_id)
    membership = Membership.objects.filter(user=request.user, workspace=workspace).first()
    if not membership:
        raise PermissionDenied("You are not a member of this workspace")
    posts = workspace.posts.all().order_by('-created_at')
    return render(request, 'accounts/workspace_detail.html', {'workspace': workspace, 'posts': posts})

@login_required
def children_workspaces(request, workspace_id):

    sub_workspaces = Workspace.objects.filter(
        parent_id=workspace_id,
        membership__user=request.user
    )

    return render(request, 'accounts/sub_workspaces.html', {
        'sub_workspaces': sub_workspaces
    })
@login_required
def create_post(request, workspace_id):
    """
    Create a new post in a workspace.
    """
    workspace = get_object_or_404(Workspace, id=workspace_id)
    membership = Membership.objects.filter(user=request.user, workspace=workspace).first()
    if not membership:
        raise PermissionDenied("You are not a member of this workspace")
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.workspace = workspace
        post.author = request.user
        post.save()
        return redirect('workspace_detail', workspace_id=workspace.id)
    return render(request, 'accounts/create_post.html', {'form': form, 'workspace': workspace})


@login_required
def post_detail(request, post_id):
    """
    Display a post and its comments, allow adding comments.
    """
    post = get_object_or_404(Post, id=post_id)
    membership = Membership.objects.filter(user=request.user, workspace=post.workspace).first()
    if not membership:
        raise PermissionDenied("You are not a member of this workspace")
    comments = Comment.objects.filter(post=post).order_by('-created_at')
    # comments = post.comments().all().order_by('created_at')
    form = CommentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post_detail', post_id=post.id)
    return render(request, 'accounts/post_detail.html', {'post': post, 'comments': comments, 'form': form})


def custom_404_view(request, exception):
    """
    Custom handler for HTTP 404 Not Found errors.
    """
    return render(request, '404.html', status=404)


def custom_403_view(request, exception):
    """
    Custom handler for HTTP 403 Forbidden errors.
    """
    return render(request, '403.html', status=403)


def custom_500_view(request):
    """
    Custom handler for HTTP 500 Internal Server errors.
    """
    return render(request, '500.html', status=500)


def custom_401_view(request):
    """
    Custom handler for HTTP 401 Unauthorized errors.
    Note: Django does NOT automatically use handler401.
    You must call this manually where needed.
    """
    return render(request, '401.html', status=401)
