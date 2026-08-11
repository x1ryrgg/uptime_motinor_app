from rest_framework.throttling import UserRateThrottle


class BurstManualCheckThrottle(UserRateThrottle):
    """Ограничение частых запросов (10 вызовов за 5 минут)"""

    scope = "manual_check_burst"


class DailyManualCheckThrottle(UserRateThrottle):
    """Суточное ограничение (1000 вызовов в день)"""

    scope = "manual_check_daily"