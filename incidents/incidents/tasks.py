from .getters import get_failure_threshold
from .models import Incidents, IncidentStatus
from celery import shared_task, current_app
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)

@shared_task(name='incidents.tasks.process_check_result_event')
def process_incident_logic(
    monitor_id: int,
    monitor_name: str,
    monitor_url: str,
    user_id: int,
    is_success: bool,
    consecutive_failures: int,
    interval_seconds: int,
    error_message: str = None,
):
    """Проверка последних результатов и создание/закрытие Инцидентов"""
    open_incident = Incidents.objects.filter(
        monitor_id=monitor_id, status=IncidentStatus.OPEN
    ).first()

    if is_success:
        if open_incident:
            logger.warning(
                f"[INCIDENT RESOLVED] Инцидент #{open_incident.id} закрыт для монитора #{monitor_id} ({monitor_url}). "
                f"Длительность: {open_incident.duration_seconds} сек."
            )
            open_incident.resolve()
    else:
        threshold = get_failure_threshold(interval_seconds=interval_seconds)
        logger.warning(
            f"[CHECK FAILED] Монитор #{monitor_id} ({monitor_url}) недоступен. "
            f"Сбой {consecutive_failures}/{threshold}. Причина: {error_message}"
        )

        if consecutive_failures >= threshold and not open_incident:
            incident = Incidents.objects.create(
                monitor_io=monitor_id,
                status=IncidentStatus.OPEN,
                cause=error_message or "Неизвестная ошибка сервера",
            )
            logger.error(
                f"[INCIDENT CREATED] Создан новый инцидент #{incident.pk} для монитора #{monitor_id} ({monitor_url}). "
                f"Порог сбоев ({threshold}) достигнут."
            )

        # не создаются Incidents 01.08
