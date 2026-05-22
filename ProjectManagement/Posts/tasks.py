from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
import base64

from Posts.models import Post, PostFile, CommentFile
from script import send_dm_by_email, upload_file_to_slack
from workspaces.models import Client

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

        files = PostFile.objects.filter(
            id__in=file_ids
        )

        context_data.update({
            'author': user,
            'client': client,
            'post': post,
        })

        html_content = render_to_string(
            "emails/new_post.html",
            context_data
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body="HTML email required.",
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email],
            cc=cc_emails,
        )

        email.attach_alternative(
            html_content,
            "text/html"
        )

        # Attach directly from storage
        for file_obj in files:

            file_obj.file.open('rb')

            email.attach(
                file_obj.file.name.split("/")[-1],
                file_obj.file.read(),
                None
            )

            file_obj.file.close()

        email.send()

        return f"Email sent to {to_email}"

    except Exception as exc:

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
def send_comment_notification_task(self, user_id, post_id, file_ids):
    """
    Async task for comment notifications

    Args:
        user_id: ID of the commenter (not User object)
        post_id: ID of the post (not Post object)
        file_ids: List of CommentFile IDs
    """
    try:


        user = User.objects.get(id=user_id)
        post = Post.objects.get(id=post_id)

        message = f"""
*New Comment on Post*

*Post:* {post.title}
*Commented by:* {user.username}
*Files attached:* {len(file_ids)}
"""

        send_dm_by_email(user.email, message)

        # Upload files if any
        if file_ids:
            upload_files_to_slack_task.delay(user_id, file_ids, 'comment')

        return f"Comment notification sent for post {post_id}"

    except (User.DoesNotExist, Post.DoesNotExist) as exc:
        raise self.retry(exc=exc, countdown=60)