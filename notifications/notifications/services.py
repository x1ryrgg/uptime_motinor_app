import logging
import requests
import ssl
import certifi
from abc import ABC, abstractmethod

from django.conf import settings
from django.core.mail import send_mail, get_connection
from .models import Notifications, NotificationReceiver, NotificationType

logger = logging.getLogger('notifications')


class BaseNotificationSender(ABC):
    """ Отправка сообщения о событии """

    @abstractmethod
    def send(self, title: str, message: str, target: str) -> bool:
        """Метод отправки сообщения пользователю """
        pass


class EmailSender(BaseNotificationSender):
    """Отправка писем через SMTP (Mail.ru)"""

    def send(self, title: str, message: str, target: str) -> bool:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"[EmailSender] Ошибка отправки письма на {target}: {e}")
            return False


class TgSender(BaseNotificationSender):
    """Отправка сообщений в Telegram Bot"""

    def send(self, title: str, message: str, target: str) -> bool:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

        # Формируем красивое форматирование с заголовком и текстом
        formatted_message = f"<b>{title}</b>\n\n{message}"

        payload = {
            "chat_id": target,
            "text": formatted_message,
            "parse_mode": "HTML",
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                return True
            logger.error(f"[TgSender] Ошибка TG API. Статус: {response.status_code}, Ответ: {response.text}")
            return False
        except Exception as e:
            logger.error(f"[TgSender] Сетевая ошибка при отправке в TG ({target}): {e}")
            return False


class NotificationService:
    """ Единый сервис для создания записи в БД и координации отправки """

    # Реестр доступных каналов отправки
    SENDERS = {
        NotificationReceiver.EMAIL: EmailSender(),
        NotificationReceiver.TELEGRAM: TgSender(),
    }

    @classmethod
    def send_and_save(
        cls,
        user_id: int,
        receiver_type: str,
        notification_type: str,
        title: str,
        message: str,
        target: str,  # email адрес или chat_id Telegram
    ) -> Notifications:
        """
        1. Создает запись уведомления в БД
        2. Вызывает нужный класс отправки
        3. Обновляет is_sent в случае успеха
        """
        # 1. Создаем уведомление со статусом is_sent=False
        notification = Notifications.objects.create(
            user_id=user_id,
            receiver_type=receiver_type,
            type=notification_type,
            title=title,
            message=message,
            is_sent=False,
        )

        sender = cls.SENDERS.get(receiver_type)
        if not sender:
            logger.error(f"[NotificationService] Неподдерживаемый тип получателя: {receiver_type}")
            return notification

        # 2. Пытаемся отправить
        is_success = sender.send(title=title, message=message, target=target)

        # 3. Фиксируем статус в БД
        if is_success:
            notification.is_sent = True
            notification.save(update_fields=["is_sent"])
            logger.info(f"[NotificationService] Уведомление #{notification.id} успешно отправлено via {receiver_type}")
        else:
            logger.warning(f"[NotificationService] Не удалось доставить уведомление #{notification.id}")

        return notification
