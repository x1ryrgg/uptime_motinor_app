import pandas as pd
from typing import List
import logging

from .getters import get_failure_threshold
from .models import Incidents, IncidentStatus
from monitors.models import Monitor, CheckResult

logger = logging.getLogger(__name__)


def process_incident_logic(monitor: Monitor, current_result: CheckResult):
    """Проверка последних результатов и создание/закрытие Инцидентов"""
    open_incident = monitor.incidents.filter(status=IncidentStatus.OPEN).first()

    if current_result.is_success:
        if monitor.consecutive_failures != 0:
            logger.info(
                f"[Monitor #{monitor.pk} - {monitor.name}] Сброс счетчика ошибок с {monitor.consecutive_failures} до 0."
            )
            monitor.consecutive_failures = 0

        if open_incident:
            logger.warning(
                f"[INCIDENT RESOLVED] Инцидент #{open_incident.id} закрыт для монитора #{monitor.pk} ({monitor.url}). "
                f"Длительность: {open_incident.duration_seconds} сек."
            )
            open_incident.resolve()
    else:
        monitor.consecutive_failures += 1
        threshold = get_failure_threshold(interval_seconds=monitor.interval_seconds)
        logger.warning(
            f"⚠[CHECK FAILED] Монитор #{monitor.id} ({monitor.url}) недоступен. "
            f"Сбой {monitor.consecutive_failures}/{threshold}. Причина: {current_result.error_message}"
        )

        if monitor.consecutive_failures >= threshold and not open_incident:
            incident = Incidents.objects.create(
                monitor=monitor,
                status=IncidentStatus.OPEN,
                cause=current_result.error_message or "Неизвестная ошибка сервера",
            )
            logger.error(
                f"🚨 [INCIDENT CREATED] Создан новый инцидент #{incident.pk} для монитора #{monitor.pk} ({monitor.url}). "
                f"Порог сбоев ({threshold}) достигнут."
            )
