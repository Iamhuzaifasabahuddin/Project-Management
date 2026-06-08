from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.urls import reverse

from Teams.models import Team
from .forms import CommentForm, PostForm, TaskForm, PrintTaskForm
from .models import Post, Comment, PostFile, CommentFile, Task
from .tasks import (
    send_post_email_task,
    send_slack_post_notification_task,
    upload_files_to_slack_task,
    send_comment_notification_task,
    send_assigned_task_email_task,
    send_task_completion_request_email_task,
    send_task_status_notification_task
)
from workspaces.models import Client, Membership
import base64


from workspaces.services import is_workspace_admin, is_workspace_member


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

    if not request.user.is_superuser:

        if not Membership.objects.filter(
                user=request.user,
                workspace=workspace
        ).exists():
            raise PermissionDenied("Not allowed")

    is_admin = (
            request.user.is_superuser or
            request.user == team.team_lead or
            is_workspace_admin(request.user, workspace)
    )

    if is_admin:
        tasks_queryset = Task.objects.filter(team=team).prefetch_related('assigned_to', 'posts').order_by('-created_at')
    else:
        tasks_queryset = Task.objects.filter(team=team, assigned_to=request.user).prefetch_related('assigned_to', 'posts').order_by('-created_at')

    context = {
        "team": team,
        "workspace": workspace,
        "client": team.client,
        "pending_tasks": tasks_queryset.filter(status='pending'),
        "awaiting_tasks": tasks_queryset.filter(status='awaiting_approval'),
        "completed_tasks": tasks_queryset.filter(status='completed'),
        "is_admin": is_admin,
    }

    if request.headers.get('HX-Request'):
        return render(request, "includes/task_list_fragment.html", context)

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

    if not request.user.is_superuser:
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not allowed")

        is_admin = Membership.objects.filter(user=request.user, workspace=workspace, role='admin').exists()
        if not is_admin and request.user not in team.members.all():
            raise PermissionDenied("Not a team member")

    form = TaskForm(request.POST or None, team=team)
    if form.is_valid():
        task = form.save(commit=False)
        task.team = team
        task.created_by = request.user
        task.save()
        form.save_m2m()

        # Reactivate client if it was archived
        if client.is_archived:
            client.is_archived = False
            client.save()

        messages.success(request, f"Task '{task.name}' created successfully.")
        task_url = request.build_absolute_uri(
            reverse('team_tasks', kwargs={'team_id': team.id})
        )
        context = {
            "task_url": task_url,
        }
        to_emails = [user.email for user in task.assigned_to.all() if user.email]
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
def task_completion_request(request, task_id):
    """
    Request completion for a task.
    Sets status to 'awaiting_approval' and emails team lead and admins.
    """
    task = get_object_or_404(Task, id=task_id)
    team = task.team
    workspace = team.client.workspace

    # Only assigned users or team lead/admin can request completion
    if not request.user.is_superuser:
        is_assigned = request.user in task.assigned_to.all()
        is_admin = (
            request.user == team.team_lead or is_workspace_admin(request.user, workspace)
        )
        if not (is_assigned or is_admin):
            raise PermissionDenied("Not assigned to this task")

    if task.status == 'completed':
        messages.info(request, "Task is already completed.")
        return redirect("team_tasks", team_id=team.id)

    task.status = 'awaiting_approval'
    task.save()

    # Get team lead and admins emails
    admin_memberships = Membership.objects.filter(workspace=workspace, role='admin').select_related('user')
    admin_emails = {m.user.email for m in admin_memberships if m.user.email}
    if team.team_lead and team.team_lead.email:
        admin_emails.add(team.team_lead.email)
    
    to_emails = list(admin_emails)

    if to_emails:
        approve_url = request.build_absolute_uri(reverse('task_approve', kwargs={'task_id': task.id}))
        decline_url = request.build_absolute_uri(reverse('task_decline', kwargs={'task_id': task.id}))
        
        context = {
            "approve_url": approve_url,
            "decline_url": decline_url,
            "task_url": request.build_absolute_uri(reverse('team_tasks', kwargs={'team_id': team.id})),
        }
        
        send_task_completion_request_email_task.delay(
            user_id=request.user.id,
            task_id=task.id,
            to_emails=to_emails,
            context_data=context
        )

    messages.success(request, f"Completion request sent for '{task.name}'.")
    return redirect("team_tasks", team_id=team.id)


@login_required
def task_approve(request, task_id):
    """
    Approve task completion.
    Only team lead or admins can approve.
    """
    task = get_object_or_404(Task, id=task_id)
    team = task.team
    workspace = team.client.workspace

    # Permission check
    is_admin = (
        request.user.is_superuser or
        request.user == team.team_lead or
        is_workspace_admin(request.user, workspace)
    )
    if not is_admin:
        raise PermissionDenied("Only admins or team leads can approve tasks.")

    task.status = 'completed'
    task.save()

    # Trigger auto-archive check for the client
    from workspaces.services import auto_archive_client_if_done
    auto_archive_client_if_done(team.client)

    # Notify assignees
    to_emails = [user.email for user in task.assigned_to.all() if user.email]
    if to_emails:
        context = {
            "task_url": request.build_absolute_uri(reverse('team_tasks', kwargs={'team_id': team.id})),
        }
        send_task_status_notification_task.delay(
            user_id=request.user.id,
            task_id=task.id,
            status="approved",
            to_emails=to_emails,
            context_data=context
        )

    messages.success(request, f"Task '{task.name}' marked as completed.")
    return redirect("team_tasks", team_id=team.id)


@login_required
def task_decline(request, task_id):
    """
    Decline task completion.
    Only team lead or admins can decline.
    """
    task = get_object_or_404(Task, id=task_id)
    team = task.team
    workspace = team.client.workspace

    # Permission check
    is_admin = (
        request.user.is_superuser or
        request.user == team.team_lead or
        is_workspace_admin(request.user, workspace)
    )
    if not is_admin:
        raise PermissionDenied("Only admins or team leads can decline tasks.")

    task.status = 'pending'
    task.save()

    # Reactivate client if it was archived
    if team.client.is_archived:
        team.client.is_archived = False
        team.client.save()

    # Notify assignees
    to_emails = [user.email for user in task.assigned_to.all() if user.email]
    if to_emails:
        context = {
            "task_url": request.build_absolute_uri(reverse('team_tasks', kwargs={'team_id': team.id})),
        }
        send_task_status_notification_task.delay(
            user_id=request.user.id,
            task_id=task.id,
            status="declined",
            to_emails=to_emails,
            context_data=context
        )

    messages.warning(request, f"Completion request for '{task.name}' declined.")
    return redirect("team_tasks", team_id=team.id)

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
    is_admin = is_workspace_admin(request.user, workspace)

    if not (is_superuser or is_admin):
        raise PermissionDenied("Not allowed")

    client = task.team.client
    task.delete()
    from workspaces.services import auto_archive_client_if_done
    auto_archive_client_if_done(client)

    messages.success(request, "Task deleted successfully.")
    return redirect("team_tasks", team_id=team_id)



@login_required
def all_user_tasks(request):
    """
    List all tasks for the logged-in user across all teams and clients.
    """
    if request.user.is_superuser:
        tasks_queryset = Task.objects.all().prefetch_related('assigned_to', 'posts', 'team__client__workspace').order_by('-created_at')
    else:
        tasks_queryset = Task.objects.filter(
            Q(assigned_to=request.user) |
            Q(created_by=request.user) |
            Q(team__team_lead=request.user) |
            Q(team__client__workspace__membership__user=request.user, team__client__workspace__membership__role='admin')
        ).distinct().prefetch_related('assigned_to', 'posts', 'team__client__workspace').order_by('-created_at')

    context = {
        "pending_tasks": tasks_queryset.filter(status='pending'),
        "awaiting_tasks": tasks_queryset.filter(status='awaiting_approval'),
        "completed_tasks": tasks_queryset.filter(status='completed'),
        "is_admin": request.user.is_superuser,  # Global admin status; per-task checks could be more granular
    }

    return render(request, 'all_tasks.html', context)


# =========================
# POSTS + COMMENTS
# =========================

@login_required
def task_posts(request, task_id):
    """
    Display all posts within a team (optional view).
    Only workspace members can view.
    """
    task = get_object_or_404(Task, id=task_id)
    team = task.team
    workspace = team.client.workspace

    if not request.user.is_superuser or not is_workspace_admin(request.user, workspace):
        if not is_workspace_member(request.user, workspace):
            raise PermissionDenied("Not allowed")


    posts = Post.objects.filter(task=task).select_related(
        'author',
        'task'
    ).prefetch_related('comments', 'files').order_by('-created_at')

    context = {
        "team": team,
        "workspace": workspace,
        "client": team.client,
        "posts": posts,
        "task": task
    }

    if request.headers.get('HX-Request'):
        return render(request, "includes/post_list_fragment.html", context)

    return render(request, "task_posts.html", context)


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

    if not request.user.is_superuser or not is_workspace_admin(request.user, workspace):

        if not is_workspace_member(request.user, workspace):
            raise PermissionDenied("Not allowed")

        if request.user not in team.members.all():
            raise PermissionDenied("Not a team member")

        # Must be assigned to task
        if task and request.user not in task.assigned_to.all():
            raise PermissionDenied("Not assigned to this task")
    tasks = Task.objects.filter(team=team)

    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():

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
        post_url = request.build_absolute_uri(
            reverse('post_detail', kwargs={'post_id': post.id})
        )

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
            client_id=team.client.id,
            post_id=post.id,
            to_email=team.team_lead.email,
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

        # send_slack_post_notification_task.delay(
        #     user_id=request.user.id,
        #     message=message,
        #     file_names=file_names
        # )
        #
        # if file_ids:
        #     upload_files_to_slack_task.delay(
        #         user_id=request.user.id,
        #         file_ids=file_ids,
        #         model_type='post'
        #     )

        messages.success(request, "Post created successfully.")
        return redirect("task_posts", task_id=task.id)

    return render(request, "create_post.html", {
        "form": form,
        "team": team,
        "task": task,
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

    team = post.task.team if post.task else None

    if not request.user.is_superuser or not is_workspace_admin(request.user, team.client.workspace):
        if not team:
            raise PermissionDenied("Post not linked to any team")

        if not is_workspace_member(request.user, team.client.workspace):
            raise PermissionDenied("Not allowed")

    comments = Comment.objects.filter(post=post).order_by("-created_at")

    form = CommentForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        with transaction.atomic():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            uploaded_files = request.FILES.getlist('files')
            file_ids = []

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    comment_file = CommentFile.objects.create(
                        comment=comment,
                        file=uploaded_file
                    )
                    file_ids.append(comment_file.id)
            post_url = request.build_absolute_uri(
                reverse('post_detail', kwargs={'post_id': post.id})
            )

            # Determine recipients
            to_email = post.author.email
            cc_emails = [
                u.email
                for u in post.task.assigned_to.all()
                if u.email and u != request.user and u.email != post.author.email
            ] if post.task else []

            context = {
                "post_url": post_url,
                "comment_content": comment.content,
            }

            send_comment_notification_task.delay(
                user_id=request.user.id,
                post_id=post.id,
                to_email=to_email,
                cc_emails=cc_emails,
                subject=f"New Comment on {post.title}",
                context_data=context,
                file_ids=file_ids
            )

            messages.success(request, "Comment posted successfully.")
            return redirect("post_detail", post_id=post.id)

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
    task = post.task if post.task else None

    is_superuser = request.user.is_superuser
    workspace = post.task.team.client.workspace if post.task else None
    is_admin = is_workspace_admin(request.user, workspace) if workspace else False
    is_author = post.author == request.user

    if not (is_superuser or is_admin or is_author):
        raise PermissionDenied("Not allowed")

    post.delete()
    messages.success(request, "Post deleted successfully.")

    if task:
        return redirect("task_posts", task_id=task.id)
    return redirect("dashboard")


@login_required
def print_task(request, team_id):
    """
    Handle creation of a print task using a form.
    Only workspace members can access.
    """
    team = get_object_or_404(Team, id=team_id)
    workspace = team.client.workspace
    client = team.client

    if not request.user.is_superuser:
        if not Membership.objects.filter(user=request.user, workspace=workspace).exists():
            raise PermissionDenied("Not allowed")

    if request.method == 'POST':
        form = PrintTaskForm(request.POST, client=client, workspace=workspace)
        if form.is_valid():
            copies = form.cleaned_data['number_of_copies']
            fmt = form.cleaned_data['format']
            address = form.cleaned_data['address']
            due_date = form.cleaned_data['due_date']
            task_name = f"Printing {copies} - {fmt}"
            description = (
                f"Number of Copies: {copies}\n"
                f"Format: {fmt}\n"
                f"Address: {address}\n"
                f"Client: {client.name}\n"
                f"Brand: {workspace.name}\n"
                f"Phone: {client.number}"
            )

            task = Task.objects.create(
                name=task_name,
                description=description,
                team=team,
                created_by=request.user,
                status='pending',
                due_date=due_date,
            )
            task.assigned_to.set([team.team_lead])
            task.save()
            task_url = request.build_absolute_uri(
                reverse('team_tasks', kwargs={'team_id': team.id})
            )
            context = {
                "task_url": task_url,
            }
            to_emails = [user.email for user in task.assigned_to.all() if user.email]
            send_assigned_task_email_task.delay(
                user_id=request.user.id,
                client_id=client.id,
                task_id=task.id,
                to_emails=to_emails,
                context_data=context
            )


            messages.success(request, f"Print task '{task_name}' created successfully.")
            return redirect("team_tasks", team_id=team.id)
    else:
        form = PrintTaskForm(client=client, workspace=workspace)

    return render(request, "print_task.html", {
        "form": form,
        "team": team,
        "workspace": workspace,
        "client": client,
    })