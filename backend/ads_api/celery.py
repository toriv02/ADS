import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_api.settings')

app = Celery('ads_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()