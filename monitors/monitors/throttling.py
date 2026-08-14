from rest_framework.throttling import UserRateThrottle


class BurstManualCheckThrottle(UserRateThrottle):
    """Ограничение частых запросов (10 вызовов за 5 минут)"""

    scope = "manual_check_burst"

    def allow_request(self, request, view):
        """
        Проверяем, есть ли у пользователя права суперпользователя.
        Если да — пропускаем без проверки лимита.
        """
        if request.user and request.user.is_superuser:
            return True

        # Для остальных — стандартная проверка
        return super().allow_request(request, view)


class DailyManualCheckThrottle(UserRateThrottle):
    """Суточное ограничение (1000 вызовов в день)"""

    scope = "manual_check_daily"

    def allow_request(self, request, view):
        """
        Проверяем, есть ли у пользователя права суперпользователя.
        Если да — пропускаем без проверки лимита.
        """
        if request.user and request.user.is_superuser:
            return True

        # Для остальных — стандартная проверка
        return super().allow_request(request, view)