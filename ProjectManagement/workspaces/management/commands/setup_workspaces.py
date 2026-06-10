import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from workspaces.models import Workspace, Membership

class Command(BaseCommand):
    help = "Create workspaces and assign users with roles"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        password = os.environ.get("USER_CREATION_PWD_LEAD")

        # --- DATA STRUCTURE ---
        WORKSPACE_CONFIG = {
            "USA": {
                "workspaces": ["Bookmarketeers", "Writersclique", "Aurora Writers", "KDP"],
                "roles": {
                    "project manager": {
                        "Aiza Ali": "aiza.ali@topsoftdigitals.pk",
                        "Ahmed Asif": "ahmed.asif@topsoftdigitals.pk",
                        "Maheen Sami": "maheen.sami@topsoftdigitals.pk",
                        "Mubashir Khan": "Mubashir.khan@topsoftdigitals.pk",
                        "Valencia Angelo": "valencia.angelo@topsoftdigitals.pk",
                        "Ahsan Javed": "ahsan.javed@topsoftdigitals.pk",
                        "Adrian Moses": "adrain.moses@topsoftdigitals.pk",
                        "Ancil Fernandes": "ancil.fernandes@topsoftdigitals.pk",
                        "Laiba Sheikh": "laiba.sheikh@topsoftdigitals.pk",
                        "Muhammad Abdullah Sheikh": "abdullah.sheikh@topsoftdigitals.pk",
                        "Wadia Salman Ghouri": "wadia.ghouri@topsoftdigitals.pk"
                    },
                    "marketing": {
                        "Yousuf Shaikh": "yousuf.sheikh@topsoftdigitals.pk",
                    },
                    "editor": {
                        "Tazeen Ali": "tazeen.hassan@topsoftdigitals.pk"
                    },
                    "designer": {
                        "Muhammad Umar": "raheel.bari@topsoftdigitals.pk",
                    },
                    "developer": {
                        "Jazib Ullah": "jazibullah@topsoftdigitals.pk"
                    },
                    "admin": {
                        "Asad Waqas": "asad.waqas@topsoftdigitals.pk",
                        "Farman Ali": "farmanali@topsoftdigitals.pk"
                    }
                }
            },
            "UK": {
                "workspaces": ["Authors Solutions", "Book Publication", "Books Publisher"],
                "roles": {
                    "project manager": {
                        "Youha": "youha.khan@topsoftdigitals.pk",
                        "Hassan Siddiqui": "hassan.siddiqui@topsoftdigitals.pk",
                        "Emaan Zaidi": "emaan.zaidi@topsoftdigitals.pk",
                        "Faarah Saif": "faarah.saif@topsoftdigitals.pk",
                        "Shahrukh Yousuf": "shahrukh.yousuf@topsoftdigitals.pk",
                        "Areeba Arzoo": "areeba.arzoo@topsoftdigitals.pk"
                    },
                    "marketing": {
                        "Yousuf Shaikh": "yousuf.sheikh@topsoftdigitals.pk",
                    },
                    "designer": {
                        "Muhammad Umar": "raheel.bari@topsoftdigitals.pk",

                    },
                    "editor":{},
                    "developer":{
                        "Jazib Ullah": "jazibullah@topsoftdigitals.pk"
                    },
                    "admin": {
                        "Suhaib Khan": "suhaib.khan@topsoftdigitals.pk",
                        "Farman Ali": "farmanali@topsoftdigitals.pk"
                    }
                }
            }
        }

        for country, data in WORKSPACE_CONFIG.items():
            self.stdout.write(self.style.NOTICE(f"Processing {country}..."))
            
            workspaces = []
            for ws_name in data["workspaces"]:
                workspace, _ = Workspace.objects.get_or_create(
                    name=ws_name,
                    defaults={'owner': User.objects.first()}
                )
                workspaces.append(workspace)
                self.stdout.write(f"  - Workspace '{ws_name}' ready.")

            for role, users in data["roles"].items():
                for full_name, email in users.items():
                    username = email.split("@")[0].lower()
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            "email": email,
                            "first_name": full_name.split()[0],
                            "last_name": " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
                        }
                    )
                    if created:
                        user.set_password(password)
                        user.save()
                        self.stdout.write(f"  - Created user: {username}")

                    # Assign to all workspaces in this country
                    for workspace in workspaces:
                        Membership.objects.get_or_create(
                            user=user,
                            workspace=workspace,
                            role=role
                        )
                        self.stdout.write(f"    - Added {username} as {role} to {workspace.name}")

        self.stdout.write(self.style.SUCCESS("Successfully setup workspaces and memberships."))
