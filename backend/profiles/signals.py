from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from profiles.models import StyleProfile, UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_companion_profiles(sender, instance, created, **kwargs):
    if not created:
        return
    UserProfile.objects.get_or_create(user=instance)
    StyleProfile.objects.get_or_create(user=instance)
