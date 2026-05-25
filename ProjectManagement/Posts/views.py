from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.urls import reverse

from Teams.models import Team
from script import client
from .forms import CommentForm, PostForm, TaskForm
from .models import Post, Comment, PostFile, CommentFile, Task
from .tasks import (
    send_post_email_task,
    send_slack_post_notification_task,
    upload_files_to_slack_task,
    send_comment_notification_task,
send_assigned_task_email_task
)
from workspaces.models import Client, Membership
import base64


def role_checker(user, workspace, role):
    """Check if user has a specific role, or is superuser"""
    if user.is_superuser:
        return True
    return Membership.objects.filter(user=user, workspace=workspace, role=role).exists()


# =========================
# TASKS
# =========================

@login_required
def team_tasks(request, team_id):
    """
    Display tasks within a team.

    - Superusers/admins/team leads can view all tasks
    - Regular members only see tasks assigned to them
    """

    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace

    # 🔐 Must belong to workspace
    if not request.user.is_superuser:

        if not Membership.objects.filter(
            user=request.user,
            workspace=workspace
        ).exists():

            raise PermissionDenied("Not allowed")

    # 🔐 Determine access level
    is_admin = (
        request.user.is_superuser or
        request.user == team.team_lead or
        Membership.objects.filter(
            user=request.user,
            workspace=workspace,
            role='admin'   # adjust if your field differs
        ).exists()
    )

    # 📌 Admins/team leads see all tasks
    if is_admin:

        tasks = Task.objects.filter(
            team=team
        ).prefetch_related(
            'assigned_to',
            'posts'
        ).order_by('-created_at')

    # 📌 Regular members only see assigned tasks
    else:

        tasks = Task.objects.filter(
            team=team,
            assigned_to=request.user
        ).prefetch_related(
            'assigned_to',
            'posts'
        ).order_by('-created_at')

    context = {
        "team": team,
        "workspace": workspace,
        "client": team.client,
        "tasks": tasks,
        "is_admin": is_admin,
    }

    return render(request, "team_tasks.html", context)

@login_required
def create_task(request, team_id):
    """
    Create a new task within a team.
    Only workspace members and team members can create.
    """
    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace
    client = team.client

    # 🔐 Permission check: must be workspace member (superusers always allowed)
    if not request.user.is_superuser:
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not allowed")

        # 🔐 Optional stricter check: must be team member or admin
        is_admin = Membership.objects.filter(user=request.user, workspace=workspace, role='admin').exists()
        if not is_admin and request.user not in team.members.all():
            raise PermissionDenied("Not a team member")


    form = TaskForm(request.POST or None, team=team)
    if form.is_valid():
        task = form.save(commit=False)
        task.team = team
        task.save()
        form.save_m2m()
        messages.success(request, f"Task '{task.name}' created successfully.")
        task_url = request.build_absolute_uri(
            reverse('team_tasks', kwargs={'team_id': team.id})
        )
        context = {
            "task_url": task_url,
        }
        to_emails = [user.email for user in task.assigned_to.all() if user.email]
        print(to_emails)
        send_assigned_task_email_task.delay(
            user_id=request.user.id,
            client_id=client.id,
            task_id=task.id,
            to_emails=to_emails,
            context_data=context
        )
        return redirect("team_tasks", team_id=team.id)

    return render(request, "create_task.html", {
        "form": form,
        "team": team,
        "workspace": workspace,
        "client": team.client
    })


@login_required
def delete_task(request, task_id):
    """
    Delete a task.
    Only superusers, workspace admins, or task creator can delete.
    """
    task = get_object_or_404(Task, id=task_id)
    team_id = task.team.id
    workspace = task.team.client.workspace

    # Permission checks
    is_superuser = request.user.is_superuser
    is_admin = role_checker(request.user, workspace, "admin")

    if not (is_superuser or is_admin):
        raise PermissionDenied("Not allowed")

    task.delete()
    messages.success(request, "Task deleted successfully.")
    return redirect("team_tasks", team_id=team_id)


# =========================
# POSTS + COMMENTS
# =========================

@login_required
def team_posts(request, team_id):
    """
    Display all posts within a team (optional view).
    Only workspace members can view.
    """
    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace

    # 🔐 Permission check: must be workspace member (superusers always allowed)
    if not request.user.is_superuser:
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not allowed")

    # Get all posts for this team
    posts = Post.objects.filter(task__team=team).select_related(
        'author',
        'task'
    ).prefetch_related('comments', 'files').order_by('-created_at')

    context = {
        "team": team,
        "workspace": workspace,
        "client": team.client,
        "posts": posts,
    }

    return render(request, "team_posts.html", context)


@login_required
def create_post(request, task_id):
    """
    Create a new post within a team.
    Posts are optional linked to tasks.
    """
    task = get_object_or_404(Task, id=task_id)
    workspace = task.team.client.workspace
    client = task.team.client
    team = task.team

    # 🔐 Permission check: must be workspace member (superusers always allowed)
    # 🔐 Permission checks
    if not request.user.is_superuser:

        # Must belong to workspace
        if not Membership.objects.filter(
                user=request.user,
                workspace=workspace
        ).exists():
            raise PermissionDenied("Not allowed")

        # Must belong to team
        if request.user not in team.members.all():
            raise PermissionDenied("Not a team member")

        # Must be assigned to task
        if task and request.user not in task.assigned_to.all():
            raise PermissionDenied("Not assigned to this task")
    tasks = Task.objects.filter(team=team)

    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():

        # Save post
        post = form.save(commit=False)
        post.author = request.user
        post.task = task

        post.save()

        uploaded_files = request.FILES.getlist('files')
        file_ids = []
        file_data = []

        for uploaded_file in uploaded_files:
            post_file = PostFile.objects.create(
                post=post,
                file=uploaded_file
            )
            file_ids.append(post_file.id)

            uploaded_file.seek(0)
            file_content = uploaded_file.read()

            file_data.append({
                'name': uploaded_file.name,
                'content': base64.b64encode(file_content).decode('utf-8'),
                'content_type': uploaded_file.content_type
            })

        # 🔥 URL (post-based)
        post_url = request.build_absolute_uri(
            reverse('post_detail', kwargs={'post_id': post.id})
        )

        memberships = Membership.objects.filter(
            workspace=workspace
        ).select_related('user')

        cc_emails = [
            u.email
            for u in task.assigned_to.all()
            if u.email and u != request.user and u.email != team.client.email
        ]

        context = {
            "post_url": post_url,
            "uploaded_files": [f.name for f in uploaded_files],
            "team_name": team.name
        }

        # ===== ASYNC TASKS =====

        send_post_email_task.delay(
            user_id=request.user.id,
            client_id=team.client.id,  # still ok for email grouping
            post_id=post.id,
            to_email=team.client.email,
            cc_emails=cc_emails,
            subject=f"[{team.name}] New Post - {post.title}",
            context_data=context,
            file_ids=file_ids
        )

        file_names = ', '.join([f.name for f in uploaded_files]) if uploaded_files else 'None'

        message = f"""
        *New Team Post Created*
        
        *Team:* {team.name}
        *Client:* {team.client.name}
        *Author:* {request.user.username}
        
        *Title:* {post.title}
        
        *Content:*
        >{post.content}
        
        *Files:* {file_names}
        
        *URL:* {post_url}
        """

        send_slack_post_notification_task.delay(
            user_id=request.user.id,
            message=message,
            file_names=file_names
        )

        if file_ids:
            upload_files_to_slack_task.delay(
                user_id=request.user.id,
                file_ids=file_ids,
                model_type='post'
            )

        messages.success(request, "Post created successfully.")
        return redirect("team_posts", team_id=team.id)

    return render(request, "create_post.html", {
        "form": form,
        "team": team,
        "workspace": workspace,
        "client": client,
        "tasks": tasks,
    })


@login_required
def post_detail(request, post_id):
    """
    Display post details and handle new comments with optional file attachments.
    Superusers can view any post.
    """
    post = get_object_or_404(Post, id=post_id)

    # Get the team from the post's task or use a fallback
    team = post.task.team if post.task else None

    # Check if user has access to this workspace (superusers always allowed)
    if not request.user.is_superuser:
        if not team:
            raise PermissionDenied("Post not linked to any team")

        if not Membership.objects.filter(
                user=request.user,
                workspace=team.client.workspace
        ).exists():
            raise PermissionDenied("Not allowed")

    # Get all comments for this post
    comments = Comment.objects.filter(post=post).order_by("-created_at")

    form = CommentForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        with transaction.atomic():
            # Save the comment
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            # Handle multiple file uploads for comment
            uploaded_files = request.FILES.getlist('files')
            file_ids = []

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    comment_file = CommentFile.objects.create(
                        comment=comment,
                        file=uploaded_file
                    )
                    file_ids.append(comment_file.id)

            # Queue async task for notification (with or without files)
            send_comment_notification_task.delay(
                user_id=request.user.id,
                post_id=post.id,
                file_ids=file_ids
            )

            messages.success(request, "Comment posted successfully.")
            return redirect("post_detail", post_id=post.id)

    # Get all files associated with the post
    post_files = post.files.all()

    return render(request, "post_detail.html", {
        "post": post,
        "post_files": post_files,
        "comments": comments,
        "form": form,
        "team": team,
    })


@login_required
def delete_post(request, post_id):
    """
    Delete a post.
    Only superusers, workspace admins, or post author can delete.
    """
    post = get_object_or_404(Post, id=post_id)
    team_id = post.task.team.id if post.task else None

    # Permission checks
    is_superuser = request.user.is_superuser
    workspace = post.task.team.client.workspace if post.task else None
    is_admin = role_checker(request.user, workspace, "admin") if workspace else False
    is_author = post.author == request.user

    if not (is_superuser or is_admin or is_author):
        raise PermissionDenied("Not allowed")

    post.delete()
    messages.success(request, "Post deleted successfully.")

    if team_id:
        return redirect("team_posts", team_id=team_id)
    return redirect("home")