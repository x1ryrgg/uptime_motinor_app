from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Monitor(models.Model):
    """Модель сайта/эндпоинта, который мы мониторим."""

    class HTTPMethod(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        HEAD = "HEAD", "HEAD"
        OPTIONS = "OPTIONS  ", "OPTIONS"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="monitors", verbose_name="Владелец"
    )
    name = models.CharField(max_length=255, verbose_name="Название сервиса")
    url = models.URLField(verbose_name="URL для проверки")
    method = models.CharField(
        max_length=10,
        choices=HTTPMethod.choices,
        default=HTTPMethod.GET,
        verbose_name="HTTP Метод",
    )
    # Интервал проверки в секундах
    interval_seconds = models.PositiveIntegerField(
        default=60, verbose_name="Интервал проверки (сек)"
    )
    # Ожидаемые параметры успешного ответа
    expected_status_code = models.PositiveSmallIntegerField(
        default=200, verbose_name="Ожидаемый HTTP статус"
    )
    expected_keyword = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Ожидаемый текст в ответе"
    )
    is_active = models.BooleanField(default=True, verbose_name="Мониторинг активен")
    is_currently_up = models.BooleanField(default=True, verbose_name="Сайт доступен")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Монитор"
        verbose_name_plural = "Мониторы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.url})"


class CheckResult(models.Model):
    """Лог каждой конкретной проверки (Time-series данные)."""

    monitor = models.ForeignKey(
        Monitor,
        on_delete=models.CASCADE,
        related_name="check_results",
        verbose_name="Монитор",
    )
    checked_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Время проверки", db_index=True
    )
    status_code = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="HTTP статус"
    )
    response_time_ms = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Время отклика (мс)"
    )

    is_success = models.BooleanField(verbose_name="Успешно?")
    error_message = models.TextField(blank=True, null=True, verbose_name="Текст ошибки")

    class Meta:
        verbose_name = "Результат проверки"
        verbose_name_plural = "Результаты проверок"
        ordering = ["-checked_at"]
        # Индекс для ускорения аналитики (поиск результатов конкретного монитора по времени)
        indexes = [
            models.Index(fields=["monitor", "-checked_at"]),
        ]

    def __str__(self):
        status = "UP" if self.is_success else "DOWN"
        return f"[{status}] {self.monitor.name} at {self.checked_at.strftime('%Y-%m-%d %H:%M:%S')}"
