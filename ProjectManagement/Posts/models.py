# Create your models here.
from django.contrib.auth.models import User
from django.db import models

from workspaces.models import Client


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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class PostFile(models.Model):
    """
    Model to store files associated with a post.
    Allows multiple files per post.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='files'  # Access via post.files.all()
    )
    file = models.FileField(
        upload_to='client_uploads/%Y/%m/',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.post.title} - {self.file.name}"

    class Meta:
        ordering = ['-uploaded_at']


class Comment(models.Model):
    """
    Model for comments on posts.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    class Meta:
        ordering = ['-created_at']


class CommentFile(models.Model):
    """
    Model to store files associated with comments.
    """
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='files'
    )
    file = models.FileField(
        upload_to='comment_uploads/%Y/%m/',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for comment by {self.comment.author.username}"

    class Meta:
        ordering = ['-uploaded_at']