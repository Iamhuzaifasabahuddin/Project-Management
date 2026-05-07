from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create sample users for testing"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        sample_users = [
            {"username": "user1", "email": "user1@example.com", "password": "test12345"},
            {"username": "user2", "email": "user2@example.com", "password": "test12345"},
            {"username": "user3", "email": "user3@example.com", "password": "test12345"},
            {"username": "designer", "email": "designer@example.com", "password": "test12345"},
        ]

        created_count = 0

        for u in sample_users:
            if not User.objects.filter(username=u["username"]).exists():
                User.objects.create_user(
                    username=u["username"],
                    email=u["email"],
                    password=u["password"],
                    is_active=True,

                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created user: {u['username']}"))
            else:
                self.stdout.write(f"User already exists: {u['username']}")

        self.stdout.write(self.style.SUCCESS(f"\nTotal new users created: {created_count}"))