import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create sample users for testing"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        users = {
            "Muhammad Umar": "raheel.bari@topsoftdigitals.pk",
            "Yousuf Shaikh": "yousuf.sheikh@topsoftdigitals.pk",
            "Tazeen Ali": "tazeen.hassan@topsoftdigitals.pk",
            "Jazib Ullah": "jazibullah@topsoftdigitals.pk",
            "Asad Waqas": "asad.waqas@topsoftdigitals.pk",
            "Suhaib Khan": "suhaib.khan@topsoftdigitals.pk",
            "Aiza Ali": "aiza.ali@topsoftdigitals.pk",
            "Ahmed Asif": "ahmed.asif@topsoftdigitals.pk",
            "Maheen Sami": "maheen.sami@topsoftdigitals.pk",
            "Mubashir Khan": "mubashir.khan@topsoftdigitals.pk",
            "Muhammad Ali": "muhammad.ali@topsoftdigitals.pk",
            "Valencia Angelo": "valencia.angelo@topsoftdigitals.pk",
            "Ukasha Asadullah": "ukasha.asadullah@topsoftdigitals.pk",
            "Ahsan Javed": "ahsan.javed@topsoftdigitals.pk",
            "Tooba Shoaib": "tooba.shoaib@topsoftdigitals.pk",
            "Adrian Moses": "adrain.moses@topsoftdigitals.pk",
            "Ancil Fernandes": "ancil.fernandes@topsoftdigitals.pk",
            "Laiba Sheikh": "laiba.sheikh@topsoftdigitals.pk",
            "Muhammad Abdullah Sheikh": "abdullah.sheikh@topsoftdigitals.pk",
            "Wadia Salman Ghouri": "wadia.ghouri@topsoftdigitals.pk",
            "Youha Khan": "youha.khan@topsoftdigitals.pk",
            "Hassan Siddiqui": "hassan.siddiqui@topsoftdigitals.pk",
            "Emaan Zaidi": "emaan.zaidi@topsoftdigitals.pk",
            "Faarah Saif": "faarah.saif@topsoftdigitals.pk",
            "Shahrukh Yousuf": "shahrukh.yousuf@topsoftdigitals.pk",
            "Areeba Arzoo": "areeba.arzoo@topsoftdigitals.pk",
        }

        created_count = 0
        password = os.environ.get("USER_CREATION_PWD_LEAD")

        for full_name, email in users.items():
            name_parts = full_name.split()

            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            username = email.split("@")[0].lower()

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                }
            )

            if created:
                user.set_password(password)
                user.is_active = True
                user.save()

                self.stdout.write(
                    self.style.SUCCESS(f"Created user: {username}")
                )
                created_count += 1
            else:
                self.stdout.write(
                    f"User already exists: {username}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal new users created: {created_count}"
            )
        )