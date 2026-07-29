import os
from celery import Celery
from celery.schedules import crontab

# дефолтный модуль настроек Django для celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


app.conf.beat_schedule = {
    "run_scheduled_monitoring_tasks": {
        "task": "monitors.tasks.run_scheduled_monitoring_tasks",
        "schedule": crontab(minute='*/1'),
    }
}