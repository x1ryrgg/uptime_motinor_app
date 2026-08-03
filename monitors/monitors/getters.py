import pandas as pd

from typing import List

from django.db.models import QuerySet

from .models import Monitor, CheckResult, HTTPMethod


def get_success_threshold(interval_seconds: int) -> float:
    """Определяет, сколько сбоев подряд нужно для открытия инцидента"""
    if interval_seconds <= 60:
        return 20
    elif interval_seconds <= 300:
        return 10
    return 5


def get_active_monitors(
    monitor_ids: List[int] = None, in_dataframe: bool = False
) -> Monitor:
    if monitor_ids:
        queryset = Monitor.objects.filter(
            id__in=monitor_ids, is_active=True
        )
    else:
        queryset = Monitor.objects.filter(is_active=True)

    if in_dataframe:
        queryset = pd.DataFrame.from_records(queryset.values())

    return queryset