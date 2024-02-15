from __future__ import absolute_import, unicode_literals
# Это будет гарантировать, что приложение всегда импортируется при запуске Django
from BrainBites.celery_config import app as celery_app

__all__ = ('celery_app',)