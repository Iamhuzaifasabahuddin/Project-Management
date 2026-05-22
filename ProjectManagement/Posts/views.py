from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.urls import reverse

from Teams.models import Team
from script import client
from .forms import CommentForm, PostForm
from .models import Post, Comment, PostFile, CommentFile
from .tasks import (
    send_post_email_task,
    send_slack_post_notification_task,
    upload_files_to_slack_task,
    send_comment_notification_task
)
from workspaces.models import Client, Membership
import base64


def role_checker(user, workspace, role):
    """Check if user has a specific role, or is superuser"""
    if user.is_superuser:
        return True
    return Membership.objects.filter(user=user, workspace=workspace, role=role).exists()


# =========================
# POSTS + COMMENTS
# =========================
@login_required
def create_post(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace
    client = team.client

    # 🔐 Permission check: must be workspace member (superusers always allowed)
    if not request.user.is_superuser:
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not allowed")

        # 🔐 Optional stricter check: must be team member
        if request.user not in team.members.all():
            raise PermissionDenied("Not a team member")

    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():

        with transaction.atomic():

            # Save post
            post = form.save(commit=False)
            post.team = team  # 🔥 FIXED HERE
            post.author = request.user
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

            # 🔥 URL (team-based now)
            post_url = request.build_absolute_uri(
                reverse('post_detail', kwargs={'post_id': post.id})
            )

            memberships = Membership.objects.filter(
                workspace=workspace
            ).select_related('user')

            cc_emails = [
                m.user.email
                for m in memberships
                if m.user.email and m.user != request.user
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

        return redirect("team_posts", team_id=team.id)

    return render(request, "create_post.html", {
        "form": form,
        "team": team,
        "workspace": workspace,
        "client": client
    })


@login_required
def post_detail(request, post_id):
    """
    Display post details and handle new comments with optional file attachments.
    Superusers can view any post.
    """
    post = get_object_or_404(Post, id=post_id)

    # Check if user has access to this workspace (superusers always allowed)
    if not request.user.is_superuser:
        if not Membership.objects.filter(
                user=request.user,
                workspace=post.team.client.workspace
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

                # Queue async task for Slack uploads and notification
                # ✅ FIXED: Pass user_id instead of user object
                send_comment_notification_task.delay(
                    user_id=request.user.id,  # ✅ Pass ID
                    post_id=post.id,
                    file_ids=file_ids
                )
            else:
                # Still notify even without files
                # ✅ FIXED: Pass user_id instead of user object
                send_comment_notification_task.delay(
                    user_id=request.user.id,  # ✅ Pass ID
                    post_id=post.id,
                    file_ids=[]
                )

        return redirect("post_detail", post_id=post.id)

    # Get all files associated with the post
    post_files = post.files.all()

    return render(request, "post_detail.html", {
        "post": post,
        "post_files": post_files,
        "comments": comments,
        "form": form,
    })


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    team_id = post.team.id

    # Superusers can delete any post
    is_superuser = request.user.is_superuser
    is_admin = role_checker(request.user, post.team.client.workspace, "admin")
    is_author = post.author == request.user

    if not (is_superuser or is_admin or is_author):
        raise PermissionDenied("Not allowed")

    post.delete()
    return redirect("team_posts", team_id=team_id)
