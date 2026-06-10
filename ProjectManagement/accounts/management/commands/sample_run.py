from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create sample users for testing"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        sample_users = [
            {"username": "marc_bm", "email": "marc.spector@bookmarketeers.net", "password": "test12345"},
            {"username": "marc_wc", "email": "marc.spector@writersclique.net", "password": "test12345"},
            {"username": "marc_aw", "email": "marc.spector@aurorawriters.com", "password": "test12345"},
            # {"username": "huzaifa", "email": "huzaifa.sabah@topsoftdigitals.pk", "password": "test12345"},
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