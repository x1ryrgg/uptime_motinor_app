from rest_framework import serializers

from monitors.models import Monitor, CheckResult


class CheckResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = CheckResult
        fields = (
            "id",
            "checked_at",
            "status_code",
            "is_success",
            "response_time_ms",
            "error_message",
        )


class MonitorSerializer(serializers.ModelSerializer):
    last_check = serializers.SerializerMethodField()

    class Meta:
        model = Monitor
        fields = (
            "id",
            "user_id",
            "name",
            "url",
            "method",
            "interval_seconds",
            "expected_status_code",
            "expected_keyword",
            'consecutive_failures',
            'consecutive_successes',
            "is_active",
            "is_currently_up",
            "created_at",
            "updated_at",
            "last_check",
        )
        read_only_fields = (
            "id",
            "is_currently_up",
            "created_at",
            "updated_at",
            "last_check",
            'consecutive_failures',
            'consecutive_successes',
        )

    def get_last_check(self, obj):
        if hasattr(obj, "prefetched_last_checks"):
            last_result = (
                obj.prefetched_last_checks[0] if obj.prefetched_last_checks else None
            )
        else:
            last_result = obj.check_results.first()

        if last_result:
            return CheckResultSerializer(last_result).data
        return None

