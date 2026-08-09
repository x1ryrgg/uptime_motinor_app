import asyncio
from celery import shared_task, current_app
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Monitor, CheckResult
from .services import execute_monitor_check, execute_monitor_check_local
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

        if result.is_success:
            if monitor.consecutive_failures != 0:
                logger.info(
                    f"[Monitor #{monitor.pk} - {monitor.name}] Сброс счетчика ошибок с {monitor.consecutive_failures} до 0."
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
        f"Завершена проверка монитора #{monitor.pk}. "
        f"Статус: {'UP' if result.is_success else 'DOWN'}, Время ответа: {result.response_time_ms}ms. Событие отправлено в RabbitMQ."
    )


@shared_task
def run_scheduled_monitoring_tasks():
    """
    Периодическая таска (запускается раз в N секунд
    Фильтрует мониторы, которым пора пройти проверку по интервалу.
    """
    logger.info(f"[run_scheduled_monitoring_tasks] Запуск отработки мониторинга")
    active_monitors = Monitor.objects.filter(is_active=True)

    now = timezone.now()

    for monitor in active_monitors:
        last_check = monitor.check_results.first()

        if not last_check or (now - last_check.checked_at) >= timedelta(
            seconds=monitor.interval_seconds
        ):
            run_single_monitor_task.delay(monitor.pk)
