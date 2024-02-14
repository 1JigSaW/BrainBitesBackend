from celery_config import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser


@shared_task
def restore_lives():
    for user in CustomUser.objects.filter(lives__lt=5):
        if timezone.now() - user.last_life_lost_time >= timedelta(minutes=1):
            user.lives += 1
            if user.lives == 5:
                user.last_life_lost_time = None
            else:
                user.last_life_lost_time = timezone.now()
            user.save()
