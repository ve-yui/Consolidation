from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def assign_user_group(sender, instance, **kwargs):
    """Keep a user's Django group aligned with the selected news role."""
    Group = apps.get_model("auth", "Group")
    group, _ = Group.objects.get_or_create(name=instance.get_role_display())
    instance.groups.set([group])
