from celery import shared_task
from .services import NotificationService
from .models import NotificationReceiver, NotificationType
from shared_logging.logging import get_logger


logger = get_logger(__name__)


@shared_task(
    name="notifications.tasks.send_incident_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def send_incident_notification_event(
        self,
        user_id: int,
        receiver_type: str,
        notification_type: str,
        target: str,
        title: str,
        message: str,
):
    """Обработчик задачи отправки уведомления из очереди RabbitMQ"""

    logger.info(
        "Processing incident notification task",
        task_id=self.request.id,
        user_id=user_id,
        receiver_type=receiver_type,
        notification_type=notification_type,
    )

    try:
        notification = NotificationService.send_and_save(
            user_id=user_id,
            receiver_type=receiver_type,
            notification_type=notification_type,
            title=title,
            message=message,
            target=target,
        )

        if not notification:
            logger.warning(
                "Incident notification was not sent or saved",
                task_id=self.request.id,
                user_id=user_id,
                receiver_type=receiver_type,
            )
            return

        logger.info(
            "Incident notification task completed successfully",
            task_id=self.request.id,
            notification_id=notification.pk,
            user_id=user_id,
        )

    except Exception as exc:
        logger.error(
            "Error processing incident notification task",
            task_id=self.request.id,
            user_id=user_id,
            receiver_type=receiver_type,
            exc_info=True,
        )
        # Отправляем таску на повтор в Celery при сбоях
        raise self.retry(exc=exc)