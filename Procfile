web: gunicorn BrainBites.wsgi --log-file - --timeout 190
worker: celery -A BrainBites worker --loglevel=info
beat: celery -A BrainBites beat --loglevel=info