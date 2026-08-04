import logging
import traceback

import requests
import ssl
import certifi
from abc import ABC, abstractmethod

from django.conf import settings
from django.core.mail import send_mail, get_connection
from .models import Notifications, NotificationReceiver, NotificationType

logger = logging.getLogger('notifications')


class BaseNotificationSender(ABC):
    """ Контракт отправки сообщения о событии """

    @abstractmethod
    def send(self, title: str, message: str, target: str) -> bool:
        """Метод отправки сообщения пользователю """
        pass


class EmailSender(BaseNotificationSender):
    """Отправка писем через SMTP """

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
            logger.error(f"[EmailSender] Ошибка отправки письма на {target}: {e} | {traceback.format_exc()}")
            return False


class TgSender(BaseNotificationSender):
    """Отправка сообщений в Telegram Bot"""

    def send(self, title: str, message: str, target: str) -> bool:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

        formatted_message = f"<b>{title}</b>\n\n{message}"

        payload = {
            "chat_id": target,
            "text": formatted_message,
            "parse_mode": "HTML",
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            logger.error(f"[TgSender] Ошибка TG API. Статус: {response.status_code}, Ответ: {response.text}")
            return False
        except Exception as e:
            logger.error(f"[TgSender] Сетевая ошибка при отправке в TG ({target}): {e}")
            return False


class BaseNotifySaver(ABC):
    """ Контракт сохранения сообщения и его статуса """

    @abstractmethod
    def create_notification(self, user_id: int,
                            notification_type: str,
                            title: str,
                            message: str,) -> Notifications | None:
        pass

    @abstractmethod
    def mark_as_sent(self, notification: Notifications):
        pass


class EmailSaver(BaseNotifySaver):
    """ Сохранение email сообщений """

    def create_notification(self, user_id: int, notification_type: str, title: str, message: str) -> Notifications | None:
        try:
            return Notifications.objects.create(
                user_id=user_id,
                receiver_type=NotificationReceiver.EMAIL,
                type=notification_type,
                title=title,
                message=message,
                is_sent=False,
            )
        except Exception as e:
            logger.error(f"[EmailSaver] Ошибка сохранения: {e}")
            return None

    def mark_as_sent(self, notification: Notifications):
        notification.complete()


class TgSaver(BaseNotifySaver):
    """ Сохранение tg сообщений """

    def create_notification(self, user_id: int, notification_type: str, title: str, message: str) -> Notifications | None:
        try:
            return Notifications.objects.create(
                user_id=user_id,
                receiver_type=NotificationReceiver.TELEGRAM,
                notification_type=notification_type,
                title=title,
                message=message,
                is_sent=False
            )
        except Exception as e:
            logger.error(f"[TgSaver] Ошибка сохранения: {e}")
            return None

    def mark_as_sent(self, notification: Notifications):
        notification.complete()


class NotificationChannel:
    """Связывает Sender и Saver для одного типа канала"""

    def __init__(self, sender: BaseNotificationSender, saver: BaseNotifySaver):
        self.sender = sender
        self.saver = saver

    def process(self, user_id: int, notification_type: str, title: str, message: str, target: str) -> Notifications | None:
        # 1. Сохраняем черновик в БД
        notification = self.saver.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message
        )

        if not notification:
            return None

        # 2. Отправляем
        if self.sender.send(title=title, message=message, target=target):
            # 3. При успехе меняем статус через Saver
            self.saver.mark_as_sent(notification)
            logger.info(f"[NotificationChannel] Уведомление #{notification.id} доставлено на {target}")
        else:
            logger.warning(f"[NotificationChannel] Ошибка доставки уведомления #{notification.id}")

        return notification


class NotificationService:
    """"Единая точка входа для всех каналов уведомлений"""

    # Реестр доступных каналов отправки
    CHANNELS: dict[str, NotificationChannel] = {
        NotificationReceiver.EMAIL: NotificationChannel(EmailSender(), EmailSaver()),
        NotificationReceiver.TELEGRAM: NotificationChannel(TgSender(), TgSaver()),
    }

    @classmethod
    def send_and_save(
        cls,
        user_id: int,
        receiver_type: str,
        notification_type: str,
        title: str,
        message: str,
        target: str,
    ) -> Notifications | None:
        channel = cls.CHANNELS.get(receiver_type)
        if not channel:
            logger.error(f"[NotificationService] Неизвестный тип получателя: {receiver_type}")
            return None

            # Передаем всю работу соответствующему каналу
        return channel.process(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            target=target,
        )
