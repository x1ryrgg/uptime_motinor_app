from .getters import get_failure_threshold
from .models import Incidents, IncidentStatus
from celery import shared_task, current_app
from shared_logging.logging import get_logger
from .grpc_client import get_user_settings_via_grpc


logger = get_logger(__name__)


def dispatch_notifications(user_id: int, notification_type: str, title: str, message: str):
    """Вспомогательная функция: запрашивает через gRPC настройки юзера и отправляет таски в RabbitMQ"""
    user_data = get_user_settings_via_grpc(user_id)
    if not user_data:
        logger.error(
            "Failed to fetch user settings via gRPC",
            user_id=user_id,
            notification_type=notification_type,
        )
        return

    CHANNELS = [
        ("email", "email_enabled", "email"),
        ("telegram_chat_id", "telegram_enabled", "telegram"),
        ("phone_number", "sms_enabled", "sms"),
    ]

    for target_field, enabled_field, receiver_type in CHANNELS:
        target = user_data.get(target_field)
        is_enabled = user_data.get(enabled_field)

        if is_enabled and target:
            current_app.send_task(
                "notifications.tasks.send_incident_notification",
                kwargs={
                    "user_id": user_id,
                    "receiver_type": receiver_type,
                    "notification_type": notification_type,
                    "target": target,
                    "title": title,
                    "message": message,
                },
                queue="notifications_queue",
            )

@shared_task(
    name='incidents.tasks.process_check_result_event',
    bind=True,
)
def process_incident_task(
    self,
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
    logger.info(
        "Processing check result event for incident handling",
        task_id=self.request.id,
        monitor_id=monitor_id,
        is_success=is_success,
        consecutive_failures=consecutive_failures,
    )

    open_incident = Incidents.objects.filter(
        monitor_id=monitor_id, status=IncidentStatus.OPEN
    ).first()

    if is_success:
        if open_incident:
            open_incident.resolve()
            logger.info(
                "Incident resolved successfully",
                task_id=self.request.id,
                incident_id=open_incident.pk,
                monitor_id=monitor_id,
                duration_seconds=open_incident.duration_seconds,
            )

            dispatch_notifications(
                user_id=user_id,
                notification_type="info",
                title=f"🟢 Восстановление: {monitor_name}",
                message=(
                    f"Монитор '{monitor_name}' ({monitor_url}) снова доступен!\n"
                    f"Длительность сбоя: {open_incident.duration_seconds} сек."
                ),
            )
    else:
        threshold = get_failure_threshold(interval_seconds=interval_seconds)
        logger.warning(
            "Monitor check failed",
            task_id=self.request.id,
            monitor_id=monitor_id,
            monitor_url=monitor_url,
            consecutive_failures=consecutive_failures,
            threshold=threshold,
            error_message=error_message,
        )

        if consecutive_failures >= threshold and not open_incident:
            incident = Incidents.objects.create(
                monitor_id=monitor_id,
                user_id=user_id,
                status=IncidentStatus.OPEN,
                cause=error_message or "Неизвестная ошибка сервера",
            )
            logger.error(
                "New incident created",
                task_id=self.request.id,
                incident_id=incident.pk,
                monitor_id=monitor_id,
                user_id=user_id,
                threshold=threshold,
                cause=incident.cause,
            )

            dispatch_notifications(
                user_id=user_id,
                notification_type="warning",
                title=f"🔴 Сбой: {monitor_name}",
                message=(
                    f"Монитор '{monitor_name}' ({monitor_url}) недоступен!\n"
                    f"Причина: {incident.cause}"
                ),
            )
