from django.contrib.auth.models import User
from django.db import models

from workspaces.models import Client


class Team(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('project manager', 'Project Manager'),
        ('marketing', 'Marketing'),
        ('designer', 'Designer'),
        ('developer', 'Developer'),
        ('editor', 'Editor'),
        ('publisher', 'Publisher'),

    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="teams"
    )

    name = models.CharField(max_length=100)

    roles = models.CharField(
        max_length=100,
        choices=ROLE_CHOICES,
        blank=True,
        null=True
    )

    team_lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_team",
        help_text="The single user responsible for managing this team."
    )

    members = models.ManyToManyField(
        User,
        related_name="teams",
        blank=True
    )

    def __str__(self):
        return f"{self.client.name} - {self.name}"
