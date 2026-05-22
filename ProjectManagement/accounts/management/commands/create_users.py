from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from workspaces.models import Membership, Workspace


class Command(BaseCommand):
    help = "Create sample users + workspace memberships for testing"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        sample_users = [
            {"username": "manager", "email": "user1@example.com", "password": "test12345", "role": "manager"},
            {"username": "editor", "email": "user2@example.com", "password": "test12345", "role": "editor"},
            {"username": "projectmanager", "email": "user3@example.com", "password": "test12345", "role": "project manager"},
            {"username": "designer", "email": "designer@example.com", "password": "test12345", "role": "designer"},
        ]

        created_count = 0

        owner = User.objects.first()
        if not owner:
            self.stdout.write(self.style.ERROR("No users exist to assign as workspace owner"))
            return

        ws, created_ws = Workspace.objects.get_or_create(
            name="Testing",
            defaults={"owner": owner},
        )

        for u in sample_users:
            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults={
                    "email": u["email"],
                }
            )

            if created:
                user.set_password(u["password"])
                user.is_active = True
                user.save()

                self.stdout.write(self.style.SUCCESS(f"Created user: {u['username']}"))
                created_count += 1
            else:
                self.stdout.write(f"User already exists: {u['username']}")

            Membership.objects.get_or_create(
                user=user,
                workspace=ws,
                defaults={
                    "role": u["role"],
                }
            )

        self.stdout.write(
            self.style.SUCCESS(f"\nTotal new users created: {created_count}")
        )