import asyncio
from celery import shared_task, current_app
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Monitor, CheckResult
from .services import execute_monitor_check, execute_monitor_check_local
from shared_logging.logging import get_logger

logger = get_logger(__name__)


@shared_task(
    name="monitors.tasks.run_single_monitor_task",
    bind=True,
)
def run_single_monitor_task(self, monitor_id: int):
    """Задача для запроса по одному мониторингу"""
    logger.info(
        "Starting monitor check task",
        task_id=self.request.id,
        monitor_id=monitor_id,
    )

    try:
        monitor = Monitor.objects.get(id=monitor_id)
    except Monitor.DoesNotExist:
        logger.warning(
            "Monitor not found for check task",
            task_id=self.request.id,
            monitor_id=monitor_id,
        )
        return {
            "status": "error",
            "error": "Monitor not found",
            "monitor_id": monitor_id,
        }

    try:
        result = asyncio.run(execute_monitor_check(monitor))
    except Exception as exc:
        logger.error(
            "Critical error during monitor execution",
            task_id=self.request.id,
            monitor_id=monitor_id,
            exc_info=True,
        )
        return

    with transaction.atomic():
        result.save()

        if result.is_success:
            if monitor.consecutive_failures != 0:
                logger.info(
                    "Resetting consecutive failures count to zero",
                    monitor_id=monitor.pk,
                    monitor_name=monitor.name,
                    previous_failures=monitor.consecutive_failures,
                )
                monitor.consecutive_failures = 0
            monitor.consecutive_successes += 1
            monitor.is_currently_up = True
        else:
            monitor.consecutive_successes = 0
            monitor.consecutive_failures += 1
            monitor.is_currently_up = False

        monitor.save(
            update_fields=[
                "consecutive_failures",
                "is_currently_up",
                "updated_at",
            ]
        )

    # Публикация события в RabbitMQ для сервиса incidents
    current_app.send_task(
        "incidents.tasks.process_check_result_event",
        kwargs={
            "monitor_id": monitor.pk,
            "monitor_name": monitor.name,
            "monitor_url": monitor.url,
            "user_id": monitor.user_id,
            "is_success": result.is_success,
            "consecutive_failures": monitor.consecutive_failures,
            "interval_seconds": monitor.interval_seconds,
            "error_message": result.error_message,
        },
        queue="incidents_queue",
    )

    logger.info(
        "Monitor check task completed successfully",
        task_id=self.request.id,
        monitor_id=monitor.pk,
        is_success=result.is_success,
        response_time_ms=result.response_time_ms,
        consecutive_failures=monitor.consecutive_failures,
    )

@shared_task
def run_scheduled_monitoring_tasks():
    """
    Периодическая таска (запускается раз в N секунд
    Фильтрует мониторы, которым пора пройти проверку по интервалу.
    """
    logger.info("Starting scheduled monitoring worker check cycle")
    active_monitors = Monitor.objects.filter(is_active=True)

    now = timezone.now()

    for monitor in active_monitors:
        last_check = monitor.check_results.first()

        if not last_check or (now - last_check.checked_at) >= timedelta(
            seconds=monitor.interval_seconds
        ):
            run_single_monitor_task.delay(monitor_id=monitor.pk)