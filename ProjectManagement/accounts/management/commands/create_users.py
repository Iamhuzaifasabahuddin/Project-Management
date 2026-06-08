import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create sample users for testing"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        sample_users = [
            {
                "username": "muhammad.umar",
                "first_name": "Muhammad",
                "last_name": "Umar",
                "email": "raheel.bari@topsoftdigitals.pk",
                "password": os.environ.get("USER_CREATION_PWD_LEAD")
            },
            {
                "username": "Yousuf.shaikh",
                "first_name": "Yousuf",
                "last_name": "Shaikh",
                "email": "yousuf.sheikh@topsoftdigitals.pk",
                "password": os.environ.get("USER_CREATION_PWD_LEAD")
            },
            {
                "username": "Tazeen.ali",
                "first_name": "Tazeen",
                "last_name": "Ali",
                "email": "tazeen.hassan@topsoftdigitals.pk",
                "password": os.environ.get("USER_CREATION_PWD_LEAD")
            },
            {
                "username": "Jazib.ullah",
                "first_name": "Jazib",
                "last_name": "Ullah",
                "email": "jazibullah@topsoftdigitals.pk",
                "password": os.environ.get("USER_CREATION_PWD_LEAD")
            },
            {
                "username": "Asad.waqas",
                "first_name": "Asad",
                "last_name": "Waqas",
                "email": "asad.waqas@topsoftdigitals.pk",
                "password": os.environ.get("USER_CREATION_PWD_LEAD")
            },
            {
                "username": "Suhaib.khan",
                "first_name": "Suhaib",
                "last_name": "Khan",
                "email": "suhaib.khan@topsoftdigitals.pk",
                "password": os.environ.get("USER_CREATION_PWD_LEAD")
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