from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser


@shared_task
def restore_lives():
    now = timezone.now()
    minute_ago = now - timedelta(seconds=50)
    users_to_restore = CustomUser.objects.filter(last_life_lost_time__lte=minute_ago, lives__lt=5)

    for user in users_to_restore:
        user.lives += 5
        user.save()


@shared_task
def clean_up_old_life_data():
    cutoff_date = timezone.now() - timedelta(days=1)
    CustomUser.objects.filter(last_life_lost_time__lt=cutoff_date, lives=5).delete()
