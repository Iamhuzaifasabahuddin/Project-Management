from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User

@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id, subject, template, context):
    try:
        user = User.objects.get(id=user_id)
        html_content = render_to_string(template, context)

        email = EmailMultiAlternatives(
            subject=subject,
            body="Please use an HTML-compatible email viewer.",
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email],
        )

        email.attach_alternative(html_content, "text/html")
        email.send()
        return f"Verification email sent to {user.email}"
    except User.DoesNotExist:
        return f"User with ID {user_id} not found"
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
