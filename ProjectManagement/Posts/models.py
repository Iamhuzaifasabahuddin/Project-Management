# Create your models here.
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from Teams.models import Team
from workspaces.models import Client
# ─────────────────────────────────────────────
#  TASKS
# ─────────────────────────────────────────────

class Task(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('completed', 'Completed'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField()
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    assigned_to = models.ManyToManyField(
        User,
        related_name="assigned_tasks",
        blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    due_date = models.DateField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team.name} - {self.name}"

    def due_status(self):
        today = timezone.localdate()
        if self.due_date < today:
            return "overdue"
        elif self.due_date == today:
            return "today"
        return "upcoming"


# ─────────────────────────────────────────────
#  POSTS (UPDATED)
# ─────────────────────────────────────────────

class Post(models.Model):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="posts",
        null=True,
        blank=True
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    title = models.CharField(max_length=255)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


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
        upload_to='post_uploads/%Y/%m/',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.post.title} - {self.file.name}"
    
    @property
    def filename(self):
        import os
        return os.path.basename(self.file.name)

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