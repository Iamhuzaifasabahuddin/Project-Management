from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create default superuser"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        if not User.objects.filter(username="Hexz").exists():
            User.objects.create_superuser(
                username="Hexz",
                email="Huzaifasabah@gmail.com",
                password="Testing1234!!",
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS("Superuser created"))
        else:
            self.stdout.write("Superuser already exists")