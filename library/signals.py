from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    profile, _ = Profile.objects.get_or_create(user=instance)
    if instance.is_superuser or instance.groups.filter(name='Librarian').exists():
        profile.role = 'librarian'
    else:
        profile.role = 'student'
    profile.save(update_fields=['role'])


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    Group.objects.get_or_create(name='Librarian')
    Group.objects.get_or_create(name='Student')
