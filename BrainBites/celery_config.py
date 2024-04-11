# celery_config.py

from __future__ import absolute_import, unicode_literals
import os
import ssl

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BrainBites.settings')

app = Celery('BrainBites')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
