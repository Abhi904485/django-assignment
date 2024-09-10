from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Video
from .tasks import process_video_into_chunks


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    if created:
        process_video_into_chunks.delay(instance.id)
