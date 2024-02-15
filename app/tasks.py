from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser


@shared_task
def restore_lives():
    now = timezone.now()
    minute_ago = now - timedelta(minutes=1)
    users_to_restore = CustomUser.objects.filter(last_life_lost_time__lte=minute_ago, lives__lt=5)

    for user in users_to_restore:
        user.lives += 1
        user.save()
