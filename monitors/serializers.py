from rest_framework import serializers

from monitors.models import Monitor, CheckResult


class CheckResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = CheckResult
        fields = (
            'id',
            'checked_at',
            'status_code',
            'response_time_ms',
            'is_success',
            'response_time_ms',
            'error_message'
        )


class MonitorSerializer(serializers.ModelSerializer):
    last_check = serializers.SerializerMethodField()
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Monitor
        fields = (
            'id',
            'user_email',
            'name',
            'url',
            'method',
            'interval_seconds',
            'expected_status_code',
            'expected_keyword',
            'is_active',
            'is_currently_up',
            'created_at',
            'updated_at',
            'last_check'
        )
        read_only_fields = ('id', 'is_currently_up', 'created_at', 'updated_at', 'last_check')

    def get_last_check(self, obj):
        last_result = obj.check_results.first()
        if last_result:
            return CheckResultSerializer(last_result).data
        return None
