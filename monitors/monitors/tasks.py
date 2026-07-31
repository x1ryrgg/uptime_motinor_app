import asyncio
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from incidents.services import process_incident_logic
from user_support.models import User
from .models import Monitor
from .services import execute_monitor_check
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task
def run_single_monitor_task(monitor_id):
    """Задача для запроса по одному мониторингу"""
    logger.info(f"[run_single_monitor_task] Запуск проверки монитора ID: {monitor_id}")

    try:
        monitor = Monitor.objects.get(id=monitor_id)
    except Monitor.DoesNotExist:
        logger.error(f"Монитор с ID {monitor_id} не найден в БД.")
        return

    try:
        result = asyncio.run(execute_monitor_check(monitor))
    except Exception as exc:
        logger.exception(
            f"[run_single_monitor_task] Критическая ошибка при выполнении проверки монитора #{monitor_id}: {exc}"
        )
        return

    with transaction.atomic():
        result.save()

        process_incident_logic(monitor=monitor, current_result=result)

        monitor.is_currently_up = result.is_success

        monitor.save(
            update_fields=[
                "consecutive_failures",
                "is_currently_up",
                "updated_at",
            ]
        )

    logger.info(
        f"Завершена проверка монитора #{monitor.pk}. "
        f"Статус: {'UP' if result.is_success else 'DOWN'}, Время ответа: {result.response_time_ms}ms"
    )


@shared_task
def run_scheduled_monitoring_tasks():
    """
    Периодическая таска (запускается раз в N секунд
    Фильтрует мониторы, которым пора пройти проверку по интервалу.
    """
    logger.info(f"[run_scheduled_monitoring_tasks] Запуск отработки мониторинга")
    active_users = User.objects.filter(is_active=True)
    active_monitors = Monitor.objects.filter(is_active=True, user__in=active_users)

    now = timezone.now()

    for monitor in active_monitors:
        last_check = monitor.check_results.first()

        if not last_check or (now - last_check.checked_at) >= timedelta(
            seconds=monitor.interval_seconds
        ):
            run_single_monitor_task.delay(monitor.pk)
