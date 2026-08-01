from rest_framework import serializers
from .models import Incidents
from monitors.serializers import OnlyMonitorSerializer
from monitors.models import Monitor


class IncidentSerializer(serializers.ModelSerializer):
    monitor = serializers.PrimaryKeyRelatedField(
        queryset=Monitor.objects.all(), write_only=True
    )
    monitor_info = OnlyMonitorSerializer(source="monitor", read_only=True)

    class Meta:
        model = Incidents
        fields = (
            "id",
            "monitor",
            "status",
            "started_at",
            "resolved_at",
            "duration_seconds",
            "cause",
            "monitor_info",
        )
        read_only_fields = ("id", "started_at", "duration_seconds")
