from django.contrib.auth.models import User
from django.db import models

from workspaces.models import Client


# from ProjectManagement.workspaces.models import Client


# Create your models here.

# ─────────────────────────────────────────────
# CLIENT POSTS (UPDATED)
# ─────────────────────────────────────────────

class Post(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='posts',
        null=True,
        blank=True
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    content = models.TextField()

    file = models.FileField(
        upload_to='client_uploads/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ─────────────────────────────────────────────
# COMMENTS (UNCHANGED LOGIC, BETTER SCOPING)
# ─────────────────────────────────────────────

class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)

    content = models.TextField()

    file = models.FileField(
        upload_to='client_uploads/comments/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"
