import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coderun2026_starter.settings')

app = Celery('coderun2026_starter')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
