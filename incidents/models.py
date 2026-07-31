from django.db import models
from django.utils import timezone



class IncidentStatus(models.TextChoices):
    """Статус инцидента - окрыт или закрыт вопрос"""

    OPEN = "OPEN", "Открыт (Сайт лежит)"
    RESOLVED = "RESOLVED", "Решён (Сайт восстановился)"


class Incidents(models.Model):
    """Модель аварии/даунтайма сайта"""

    monitor_id = models.BigIntegerField(db_index=True, verbose_name="ID Мониторинга")
    status = models.CharField(
        max_length=20,
        choices=IncidentStatus.choices,
        default=IncidentStatus.OPEN,
        db_index=True,
        verbose_name="Текущий статус урла",
    )
    started_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Время начала аварии", db_index=True
    )
    resolved_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Время восстановления"
    )
    cause = models.TextField(verbose_name="Информация по инциденту")

    class Meta:
        verbose_name = "Инцидент"
        verbose_name_plural = "Инциденты"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Incident #{self.pk} on monitor {self.monitor.name}, [{self.status}]"

    @property
    def duration_seconds(self) -> int | None:
        """Возвращает время открытого инцидента"""
        if not self.started_at:
            return None
        end_time = self.resolved_at or timezone.now()
        return int((end_time - self.started_at).total_seconds())

    def resolve(self):
        """Вспомогательный метод для закрытия инцидента"""
        self.status = IncidentStatus.RESOLVED
        self.resolved_at = timezone.now()
        self.save()
