import asyncio
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from user_support.models import User
from.models import Monitor
from .services import execute_monitor_check


@shared_task
def run_single_monitor_task(monitor_id):
    """ Задача для запроса по одному мониторингу """

    try:
        monitor = Monitor.objects.get(id=monitor_id)
    except Monitor.DoesNotExist:
        return

    result = asyncio.run(execute_monitor_check(monitor))

    result.save()

    if monitor.is_currently_up != result.is_success:
        monitor.is_currently_up = result.is_success
        monitor.save(update_fields=["is_currently_up", 'updated_at'])


@shared_task
def run_scheduled_monitoring_tasks():
    """
    Периодическая таска (запускается раз в N секунд
    Фильтрует мониторы, которым пора пройти проверку по интервалу.
    """
    active_users = User.objects.filter(is_active=True)
    active_monitors = Monitor.objects.filter(is_active=True, user__in=active_users)

    now = timezone.now()

    for monitor in active_monitors:
        last_check = monitor.check_results.first()

        if not last_check or (now - last_check.checked_at) >= timedelta(seconds=monitor.interval_seconds):
            run_single_monitor_task.delay(monitor.id)


