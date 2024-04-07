# celery_config.py

from __future__ import absolute_import, unicode_literals
import os
import ssl

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BrainBites.settings')

app = Celery('BrainBites')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_use_ssl = {'ssl_cert_reqs': ssl.CERT_NONE}

app.autodiscover_tasks()
