# =========================
# IMPORTS
# =========================

from allauth.account.forms import default_token_generator

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .forms import (
    RegisterForm,
    WorkspaceForm,
    RoleAssignForm,
    PostForm,
    CommentForm,
    ClientForm,
)

from .models import Workspace, Membership, Post, Comment, Client


# =========================
# EMAIL HELPER
# =========================

def send_custom_email(user, subject, template, context):
    html_content = render_to_string(template, context)

    email = EmailMultiAlternatives(
        subject=subject,
        body="Please use an HTML-compatible email viewer.",
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()


# =========================
# AUTH FLOW
# =========================

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            activation_link = request.build_absolute_uri(
                f"/activate/{uid}/{token}/"
            )

            send_custom_email(
                user=user,
                subject="Verify your account",
                template="emails/verify_account.html",
                context={
                    "name": user.first_name,
                    "activation_link": activation_link,
                },
            )

            messages.success(
                request,
                "Account created! Please verify your email.",
            )
            return redirect("login")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Account activated successfully.")
        return redirect("login")

    return render(request, "accounts/activation_failed.html")


def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = User.objects.filter(username=username).first()

        if not user or not user.check_password(password):
            error = "Invalid credentials."
        elif not user.is_active:
            error = "Please verify your email."
        else:
            login(request, user)
            return redirect("dashboard")

    return render(request, "accounts/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")


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

    return render(request, "accounts/dashboard.html", {
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

    return render(request, "accounts/create_workspace.html", {"form": form})


@login_required
def workspace_list(request):
    return render(request, "accounts/workspace_list.html", {
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

    return render(request, "accounts/workspace_detail.html", {
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

    return render(request, "accounts/assign_role.html", {"form": form})


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
        return redirect("workspace_detail", workspace_id=workspace.id)

    return render(request, "accounts/create_client.html", {
        "form": form,
        "workspace": workspace,
    })


@login_required
def client_list(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    return render(request, "accounts/client_list.html", {
        "clients": Client.objects.filter(workspace=workspace),
        "workspace": workspace,
    })


@login_required
def client_detail(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)

    if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
        raise PermissionDenied("Not a member")

    return render(request, "accounts/client_details.html", {
        "workspace": workspace,
        "clients": Client.objects.filter(workspace=workspace),
    })


@login_required
def client_posts(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    return render(request, "accounts/client_posts.html", {
        "client": client,
        "posts": client.posts.all().order_by("-created_at"),
    })


# =========================
# POSTS + COMMENTS
# =========================

@login_required
def create_post(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    workspace = client.workspace

    if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
        raise PermissionDenied("Not allowed")

    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.client = client
        post.author = request.user
        post.save()
        return redirect("client_detail", workspace_id=workspace.id)

    return render(request, "accounts/create_post.html", {
        "form": form,
        "client": client,
        "workspace": workspace,
    })


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not Membership.objects.filter(
        user=request.user,
        workspace=post.client.workspace
    ).exists():
        raise PermissionDenied("Not allowed")

    comments = Comment.objects.filter(post=post).order_by("-created_at")

    form = CommentForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect("post_detail", post_id=post.id)

    return render(request, "accounts/post_detail.html", {
        "post": post,
        "comments": comments,
        "form": form,
    })


# =========================
# ERROR HANDLERS
# =========================

def custom_404_view(request, exception):
    return render(request, "404.html", status=404)


def custom_403_view(request, exception):
    return render(request, "403.html", status=403)


def custom_500_view(request):
    return render(request, "500.html", status=500)


def custom_401_view(request):
    return render(request, "401.html", status=401)