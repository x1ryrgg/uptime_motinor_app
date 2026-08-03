from celery import shared_task
from .services import NotificationService
from .models import NotificationReceiver, NotificationType


@shared_task(name="notifications.tasks.send_incident_notification")
def send_incident_notification_event(
        user_id: int,
        receiver_type: str,
        notification_type: str,
        target: str,
        title: str,
        message: str,
):
    """Обработчик задачи отправки уведомления из очереди RabbitMQ"""

    NotificationService.send_and_save(
        user_id=user_id,
        receiver_type=receiver_type,
        notification_type=notification_type,
        title=title,
        message=message,
        target=target,
    )