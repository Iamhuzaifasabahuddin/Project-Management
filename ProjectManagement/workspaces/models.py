from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

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
    notes = models.TextField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name

    def outstanding(self):
        net = self.total_amount - self.amount_paid
        return net if net > 0 else 0


# ─────────────────────────────────────────────
# MEMBERSHIP
# ─────────────────────────────────────────────

class Membership(models.Model):
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
        return f"{self.role}"
