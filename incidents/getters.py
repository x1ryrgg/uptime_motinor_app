from typing import List
import pandas as pd
from django.db.models import QuerySet
from pandas import DataFrame

from .models import Incidents, IncidentStatus
from monitors.models import Monitor, CheckResult


def get_failure_threshold(interval_seconds: int) -> int:
    """Определяет, сколько сбоев подряд нужно для открытия инцидента"""
    if interval_seconds <= 60:
        return 6
    elif interval_seconds <= 300:
        return 3
    return 1


def get_active_monitors(
    monitor_ids: List[int] = None, in_dataframe: bool = False
) -> QuerySet[Monitor, Monitor] | DataFrame:
    if monitor_ids:
        queryset = Monitor.objects.select_related("user").filter(
            id__in=monitor_ids, is_active=True
        )
    else:
        queryset = Monitor.objects.select_related("user").filter(is_active=True)

    if in_dataframe:
        queryset = pd.DataFrame.from_records(queryset.values())

    return queryset
