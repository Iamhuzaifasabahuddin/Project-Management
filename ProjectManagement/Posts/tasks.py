from celery import shared_task
from celery.exceptions import Reject
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.contrib.auth.models import User
import base64

from Posts.models import Post, PostFile, CommentFile, Task
from script import send_dm_by_email, upload_file_to_slack
from workspaces.models import Client


@shared_task(bind=True, max_retries=3)
def send_task_status_notification_task(
        self,
        user_id,
        task_id,
        status,
        to_emails,
        context_data,
):
    try:
        task = Task.objects.get(id=task_id)
        user = User.objects.get(id=user_id)
        email_context = context_data.copy()
        email_context.update({
            "task_name": task.name,
            "status": status,
            "team_name": task.team.name,
        })

        template_name = "emails/task_approved.html" if status == "approved" else "emails/task_declined.html"

        if status == "approved":
            email_context.update({
                "approved_by": user.username,
            })
        else:
            email_context.update({
                "declined_by": user.username,
            })
        subject = f"Task {status.capitalize()}: {task.name}"

        html_content = render_to_string(template_name, email_context)

        email = EmailMultiAlternatives(
            subject=subject,
            body="HTML email required.",
            from_email=settings.EMAIL_HOST_USER,
            to=to_emails,

        )

        email.attach_alternative(html_content, "text/html")
        email.send()

        return f"Status notification ({status}) sent to {to_emails}"

    except Exception as exc:
        if isinstance(exc, TypeError) and "JSON serializable" in str(exc):
            raise Reject(exc, requeue=False)
        
        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1)
        )

@shared_task(bind=True, max_retries=3)
def send_task_completion_request_email_task(
        self,
        user_id,
        task_id,
        to_emails,
        context_data,
):
    try:
        user = User.objects.get(id=user_id)
        task = Task.objects.get(id=task_id)

        email_context = context_data.copy()
        email_context.update({
            "requester_name": user.get_full_name() or user.username,
            "task_name": task.name,
            "task_id": task.id,
            "team_name": task.team.name,
        })

        html_content = render_to_string(
            "emails/task_completion_request.html",
            email_context
        )

        email = EmailMultiAlternatives(
            subject=f"Completion Request: {task.name}",
            body="HTML email required.",
            from_email=settings.EMAIL_HOST_USER,
            to=to_emails,
        )

        email.attach_alternative(html_content, "text/html")
        email.send()

        return f"Completion request email sent to {to_emails}"

    except Exception as exc:
        if isinstance(exc, TypeError) and "JSON serializable" in str(exc):
            raise Reject(exc, requeue=False)
        
        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1)
        )

@shared_task(bind=True, max_retries=3)
def send_assigned_task_email_task(
        self,
        user_id,
        client_id,
        task_id,
        to_emails,
        context_data,
):
    try:
        user = User.objects.get(id=user_id)
        client = Client.objects.get(id=client_id)
        task = Task.objects.get(id=task_id)

        # ✅ Create a copy to avoid modifying task kwargs in place
        # This prevents serialization errors if the task retries.
        email_context = context_data.copy()
        email_context.update({
            "author_name": user.get_full_name() or user.username,
            "client_name": client.name,
            "task_name": task.name,
            "task_id": task.id,
            "task_description": task.description,
            "due_date": task.due_date,
        })

        html_content = render_to_string(
            "emails/new_task.html",
            email_context
        )

        email = EmailMultiAlternatives(
            subject=f"New Task: {task.name}",
            body="HTML email required.",
            from_email=settings.EMAIL_HOST_USER,
            to=to_emails,
        )

        email.attach_alternative(html_content, "text/html")
        email.send()

        return f"Email sent to {to_emails}"

    except Exception as exc:
        # If it's a serialization error, don't retry as it will keep failing
        if isinstance(exc, TypeError) and "JSON serializable" in str(exc):
            raise Reject(exc, requeue=False)
        
        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1)
        )


@shared_task(bind=True, max_retries=3)
def send_post_email_task(
        self,
        user_id,
        client_id,
        post_id,
        to_email,
        cc_emails,
        subject,
        context_data,
        file_ids
):
    try:
        user = User.objects.get(id=user_id)
        client = Client.objects.get(id=client_id)
        post = Post.objects.get(id=post_id)

        files = PostFile.objects.filter(id__in=file_ids)


        email_context = context_data.copy()
        
        file_urls = []

        for file_obj in files:
            url = file_obj.file.url
            if not url.startswith('http'):
                url = f"http://{settings.DOMAIN}{url}"
            file_urls.append({
                'name': file_obj.file.name.split("/")[-1],
                'url': url
            })

        email_context.update({

            'author': user,
            'client': client,
            'post': post,
            'file_urls': file_urls
        })

        html_content = render_to_string(
            "emails/new_post.html",
            email_context
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body="HTML email required.",
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email],
            cc=cc_emails,
        )

        email.attach_alternative(html_content, "text/html")

        email.send()

        return f"Email sent to {to_email}"

    except Exception as exc:
        if isinstance(exc, TypeError) and "JSON serializable" in str(exc):
            raise Reject(exc, requeue=False)
            
        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1)
        )

@shared_task(bind=True, max_retries=3)
def send_slack_post_notification_task(self, user_id, message, file_names):
    """
    Async task to send Slack DM and upload files

    Args:
        user_id: ID of the user (not User object)
        message: Message text to send
        file_names: List of file names that were uploaded
    """
    try:
        # Fetch user using ID
        user = User.objects.get(id=user_id)

        # Send DM notification
        send_dm_by_email(user.email, message)

        return f"Slack notification sent for user {user.email}"

    except User.DoesNotExist as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def upload_files_to_slack_task(self, user_id, file_ids, model_type='post'):
    """
    Async task to upload files to Slack

    Args:
        user_id: ID of the user (not User object)
        file_ids: List of PostFile or CommentFile IDs
        model_type: Either 'post' or 'comment'
    """
    try:
        # Fetch user using ID
        user = User.objects.get(id=user_id)

        if model_type == 'post':

            files = PostFile.objects.filter(id__in=file_ids)
        else:

            files = CommentFile.objects.filter(id__in=file_ids)

        for file_obj in files:
            upload_file_to_slack(user.email, file_obj.file)

        return f"Uploaded {len(file_ids)} files to Slack"

    except User.DoesNotExist as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_comment_notification_task(
        self,
        user_id,
        post_id,
        to_email,
        cc_emails,
        subject,
        context_data,
        file_ids,
):
    try:
        user = User.objects.get(id=user_id)
        post = Post.objects.get(id=post_id)

        files = CommentFile.objects.filter(id__in=file_ids)

        email_context = context_data.copy()
        
        file_urls = []
        for file_obj in files:
            # Assuming file_obj.file is an S3 file field
            # We generate a public/temporary URL. If AWS_QUERYSTRING_AUTH is True,
            # this generates a presigned URL automatically.
            url = file_obj.file.url
            if not url.startswith('http'):
                url = f"http://{settings.DOMAIN}{url}"
            file_urls.append({
                'name': file_obj.file.name.split("/")[-1],
                'url': url
            })
            
        email_context.update({
            'commenter': user,
            'post': post,
            'file_urls': file_urls
        })

        html_content = render_to_string(
            "emails/new_comment.html",
            email_context
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body="HTML email required.",
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email],
            cc=cc_emails,
        )

        email.attach_alternative(html_content, "text/html")

        email.send()

        return f"Comment notification email sent to {to_email}"

    except Exception as exc:
        if isinstance(exc, TypeError) and "JSON serializable" in str(exc):
            raise Reject(exc, requeue=False)

        raise self.retry(
            exc=exc,
            countdown=60 * (self.request.retries + 1)
        )