from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

from news.models import Publisher, User


class Command(BaseCommand):
    help = "Create demo roles, users, and a publisher for capstone evaluation."

    def handle(self, *args, **options):
        role_permissions = {
            "Reader": {"models": ["article", "newsletter"], "actions": ["view"]},
            "Editor": {
                "models": ["article", "newsletter"],
                "actions": ["view", "change", "delete"],
            },
            "Journalist": {
                "models": ["article", "newsletter"],
                "actions": ["add", "view", "change", "delete"],
            },
        }
        for group_name, config in role_permissions.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            for model_name in config["models"]:
                for action in config["actions"]:
                    permission = Permission.objects.filter(
                        content_type__app_label="news",
                        codename=f"{action}_{model_name}",
                    ).first()
                    if permission:
                        group.permissions.add(permission)

        accounts = [
            ("demo_editor", "EditorPass123!", User.Role.EDITOR),
            ("demo_journalist", "JournalistPass123!", User.Role.JOURNALIST),
            ("demo_reader", "ReaderPass123!", User.Role.READER),
        ]
        for username, password, role in accounts:
            user, created = User.objects.get_or_create(
                username=username, defaults={"role": role}
            )
            user.role = role
            user.set_password(password)
            user.save()
            if created:
                self.stdout.write(f"Created {role}: {username}")
            else:
                self.stdout.write(f"Updated {role}: {username}")

        publisher, _ = Publisher.objects.get_or_create(
            name="Pottery Daily",
            defaults={"description": "Demo arts publisher for evaluation."},
        )
        publisher.editors.set([User.objects.get(username="demo_editor")])
        publisher.journalists.set([User.objects.get(username="demo_journalist")])
        self.stdout.write(self.style.SUCCESS("Demo data is ready for evaluation."))
