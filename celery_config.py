from celery import Celery
from celery.schedules import crontab

app = Celery('your_project_name')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'restore-lives-every-minute': {
        'task': 'app.tasks.restore_lives',
        'schedule': crontab(minute='*/1'),
    },
}