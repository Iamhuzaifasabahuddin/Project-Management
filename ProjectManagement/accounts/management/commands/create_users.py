from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create sample users for testing"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        sample_users = [
            {
                "username": "zeeshan.rajput",
                "first_name": "Zeeshan",
                "last_name": "Rajput",
                "email": "zeeshan.rajput@topsoftdigitals.pk",
                "password": "test12345"
            },
            {
                "username": "ammar.naveed",
                "first_name": "Ammar",
                "last_name": "Naveed",
                "email": "user2@example.com",
                "password": "test12345"
            },
            {
                "username": "muhammad.umar",
                "first_name": "Muhammad",
                "last_name": "Umar",
                "email": "user3@example.com",
                "password": "test12345"
            },
            {
                "username": "farman.ali",
                "first_name": "Farman",
                "last_name": "Ali",
                "email": "designer@example.com",
                "password": "test12345"
            },
            {
                "username": "farman.ali",
                "first_name": "Farman",
                "last_name": "Ali",
                "email": "designer@example.com",
                "password": "test12345"
            },
            {
                "username": "farman.ali",
                "first_name": "Farman",
                "last_name": "Ali",
                "email": "designer@example.com",
                "password": "test12345"
            },
            {
                "username": "farman.ali",
                "first_name": "Farman",
                "last_name": "Ali",
                "email": "designer@example.com",
                "password": "test12345"
            },
        ]

        created_count = 0

        for u in sample_users:
            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults={
                    "email": u["email"],
                    "first_name": u["first_name"],
                    "last_name": u["last_name"],
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