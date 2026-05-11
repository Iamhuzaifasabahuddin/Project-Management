from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Workspace(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────

class Client(models.Model):
    Payment_method = (
        ('card', 'Card'),
        ('wire transfer', 'Wire Transfer'),
        ('cheque', 'Cheque'),
    )

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="clients"
    )

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    email = models.EmailField()

    paid = models.BooleanField(default=False)
    amount_paid = models.DecimalField(decimal_places=2, max_digits=20)
    paid_type = models.CharField(choices=Payment_method, max_length=20)

    payment_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(decimal_places=2, max_digits=20)

    assigned_to = models.ManyToManyField(
        User,
        related_name="clients"
    )

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
# MEMBERSHIP
# ─────────────────────────────────────────────

class Membership(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('member', 'Member'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'workspace', 'role'],
                name='unique_user_workspace_role'
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.workspace} ({self.role})"
