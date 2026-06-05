import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create default superusers"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        superusers = [
            {
                "username": "Hexz",
                "email": os.environ.get("SUPERUSER_EMAIL"),
                "password": os.environ.get("SUPERUSER_PASSWORD"),
            },
            {
                "username": "Farman",
                "email": os.environ.get("SUPERUSER_EMAIL_2"),
                "password": os.environ.get("SUPERUSER_PASSWORD_2"),
            },
        ]

        for user_data in superusers:
            username = user_data["username"]

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Superuser '{username}' already exists"
                    )
                )
                continue

            User.objects.create_superuser(
                username=username,
                email=user_data["email"],
                password=user_data["password"],
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser '{username}' created successfully"
                )
            )