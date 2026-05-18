from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction

from .forms import CommentForm, PostForm
from .models import Post, Comment, PostFile, CommentFile
from workspaces.models import Client, Membership
from script import send_dm_by_email, upload_file_to_slack


# Create your views here.


# =========================
# POSTS + COMMENTS
# =========================

@login_required
def create_post(request, client_id):
    """
    Create a new post with optional multiple file attachments.
    """
    client = get_object_or_404(Client, id=client_id)
    workspace = client.workspace

    # Check if user has access to this workspace
    if not Membership.objects.filter(
            user=request.user,
            workspace=workspace
    ).exists():
        raise PermissionDenied("Not allowed")

    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        # Use transaction to ensure post and files are created together
        with transaction.atomic():
            # Save the post
            post = form.save(commit=False)
            post.client = client
            post.author = request.user
            post.save()

            # Handle multiple file uploads
            uploaded_files = request.FILES.getlist('files')

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    PostFile.objects.create(
                        post=post,
                        file=uploaded_file
                    )

            # Prepare file list for notification
            file_names = ', '.join([f.name for f in uploaded_files]) if uploaded_files else 'None'

            # Create Slack message
            message = f"""
*New Post Created*

*Author:* {request.user.username}
*Client:* {client.name}

*Title:* {post.title}

*Content:*
>{post.content}

*Files Attached:* {file_names}
"""

            # Send notification
            send_dm_by_email(request.user.email, message)

            # Upload files to Slack if they exist
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    upload_file_to_slack(
                        request.user.email,
                        uploaded_file
                    )

        return redirect(
            "client_details",
            workspace_id=workspace.id
        )

    return render(request, "create_post.html", {
        "form": form,
        "client": client,
        "workspace": workspace,
    })


@login_required
def post_detail(request, post_id):
    """
    Display post details and handle new comments with optional file attachments.
    """
    post = get_object_or_404(Post, id=post_id)

    # Check if user has access to this workspace
    if not Membership.objects.filter(
            user=request.user,
            workspace=post.client.workspace
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

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    CommentFile.objects.create(
                        comment=comment,
                        file=uploaded_file
                    )

                # Upload to Slack if files exist
                for uploaded_file in uploaded_files:
                    upload_file_to_slack(
                        request.user.email,
                        uploaded_file
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
def delete_post_file(request, file_id):
    """
    Delete a specific file from a post.
    """
    post_file = get_object_or_404(PostFile, id=file_id)
    post_id = post_file.post.id

    # Check permissions
    if not Membership.objects.filter(
            user=request.user,
            workspace=post_file.post.client.workspace
    ).exists():
        raise PermissionDenied("Not allowed")

    # Only author or admin can delete
    if request.user != post_file.post.author:
        raise PermissionDenied("You can only delete your own files")

    # Delete the file
    post_file.delete()

    return redirect("post_detail", post_id=post_id)


@login_required
def delete_comment_file(request, file_id):
    """
    Delete a specific file from a comment.
    """
    comment_file = get_object_or_404(CommentFile, id=file_id)
    post_id = comment_file.comment.post.id

    # Check permissions
    if not Membership.objects.filter(
            user=request.user,
            workspace=comment_file.comment.post.client.workspace
    ).exists():
        raise PermissionDenied("Not allowed")

    # Only comment author can delete
    if request.user != comment_file.comment.author:
        raise PermissionDenied("You can only delete your own files")

    # Delete the file
    comment_file.delete()

    return redirect("post_detail", post_id=post_id)