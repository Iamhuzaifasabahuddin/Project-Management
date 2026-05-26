from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create sample users for testing"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        sample_users = [
            {"username": "manager", "email": "user1@example.com", "password": "test12345"},
            {"username": "editor", "email": "user2@example.com", "password": "test12345"},
            {"username": "projectmanager", "email": "user3@example.com", "password": "test12345"},
            {"username": "designer", "email": "designer@example.com", "password": "test12345"},
        ]

        created_count = 0

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

        self.stdout.write(
            self.style.SUCCESS(f"\nTotal new users created: {created_count}")
        )