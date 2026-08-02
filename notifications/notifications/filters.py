# notifications/filters.py
from django_filters import rest_framework as filters
from .models import Notifications


class NotificationFilter(filters.FilterSet):
    # Фильтрация по дате (от и до)
    created_at_after = filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at_before = filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Notifications
        fields = [
            "receiver_type",  # Фильтр по каналу (email, telegram, etc.)
            "type",           # Фильтр по типу (info, warning, update)
            "created_at_after",
            "created_at_before",
        ]