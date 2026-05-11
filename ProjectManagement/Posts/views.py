from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect

from .forms import CommentForm, PostForm
from .models import Post, Comment
from workspaces.models import Client, Membership

# Create your views here.


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

    return render(request, "create_post.html", {
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

    return render(request, "post_detail.html", {
        "post": post,
        "comments": comments,
        "form": form,
    })

