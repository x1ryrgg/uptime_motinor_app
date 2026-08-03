from django.db import models


class NotificationReceiver(models.TextChoices):
    EMAIL = "email"
    TELEGRAM = "telegram"
    SMS = "sms"

class NotificationType(models.TextChoices):
    INFO = "info"
    WARNING = "warning"
    UPDATE = "update"

class Notifications(models.Model):
    user_id = models.BigIntegerField(db_index=True, verbose_name="ID Владельца")
    receiver_type = models.CharField(max_length=20,
                                     choices=NotificationReceiver.choices,
                                     default=NotificationReceiver.EMAIL,
                                     db_index=True)
    type = models.CharField(max_length=20,
                            choices=NotificationType.choices,
                            default=NotificationType.INFO,
                            db_index=True)
    title = models.CharField(max_length=255, verbose_name="Заголовок/Тема")
    message = models.TextField(verbose_name="Текст сообщения")
    is_sent = models.BooleanField(default=False, verbose_name="Отправлено")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return f"[{self.type}] to user #{self.user_id} via {self.receiver_type} (Sent: {self.is_sent})"
