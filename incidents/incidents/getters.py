from typing import List

from .models import Incidents, IncidentStatus


def get_failure_threshold(interval_seconds: int) -> int:
    """Определяет, сколько сбоев подряд нужно для открытия инцидента"""
    if interval_seconds <= 60:
        return 6
    elif interval_seconds <= 300:
        return 3
    return 1

