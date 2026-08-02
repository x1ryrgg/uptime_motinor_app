from django.db import models


class NotificationReceiver(models.TextChoices):
    EMAIL = "email"
    TELEGRAM = "telegram"
    SMS = "sms"
    ALL = "all"

class NotificationType(models.TextChoices):
    INFO = "info"
    WARNING = "warning"
    UPDATE = "update"

class Notifications(models.Model):
    user_id = models.BigIntegerField(db_index=True, verbose_name="ID Владельца")
    receiver_type = models.CharField(max_length=20,
                                     choices=NotificationReceiver.choices,
                                     default=NotificationReceiver.EMAIL,
                                     null=False, db_index=True)
    type = models.CharField(max_length=20,
                            choices=NotificationType.choices,
                            default=NotificationType.INFO,
                            null=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return (f"Message to user_id: {self.user_id} | Receiver {self.receiver_type} and type: {self.type} | "
                f"created_at: {self.created_at}")
