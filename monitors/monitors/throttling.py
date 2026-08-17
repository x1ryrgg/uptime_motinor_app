from rest_framework.throttling import SimpleRateThrottle


class SuperuserExemptThrottle(SimpleRateThrottle):
    """
    Базовый троттлер, который пропускает суперпользователей.
    """

    def allow_request(self, request, view):
        if request.user and request.user.is_superuser:
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        if request.user and request.user.is_superuser:
            return None
        return self._get_cache_key(request)

    def _get_cache_key(self, request):
        """Метод для переопределения в дочерних классах"""
        raise NotImplementedError("Subclasses must implement _get_cache_key()")


class BurstManualCheckThrottle(SuperuserExemptThrottle):
    """Ограничение частых запросов (10 вызовов за 5 минут)"""

    scope = "manual_check_burst"

    def allow_request(self, request, view):
        if request.user and request.user.is_superuser:
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        if request.user and request.user.is_superuser:
            return None
        return f"throttle_{self.scope}_{request.user.id}"


class DailyManualCheckThrottle(SuperuserExemptThrottle):
    """Суточное ограничение (1000 вызовов в день)"""

    scope = "manual_check_daily"

    def allow_request(self, request, view):
        if request.user and request.user.is_superuser:
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        if request.user and request.user.is_superuser:
            return None
        return f"throttle_{self.scope}_{request.user.id}"