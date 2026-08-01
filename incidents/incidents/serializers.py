from rest_framework import serializers
from .models import Incidents


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incidents
        fields = (
            "id",
            "monitor_id",
            "status",
            "started_at",
            "resolved_at",
            "duration_seconds",
            "cause",
        )
        read_only_fields = ("id", "started_at", "duration_seconds")
