from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    telegram_chat_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Telegram Chat ID"
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserSettings(models.Model):
    user = models.OneToOneField(
        "User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="settings",
        verbose_name="User ID",
    )
    email_notification_enabled = models.BooleanField(
        default=True, verbose_name="Email Notification Enabled"
    )
    telegram_notification_enabled = models.BooleanField(
        default=False, verbose_name="Telegram Notification Enabled"
    )
    sms_notification_enabled = models.BooleanField(
        default=False, verbose_name="Sms Motification Enabled"
    )

    class Meta:
        verbose_name = "User Settings"
        verbose_name_plural = "Users Settings"
