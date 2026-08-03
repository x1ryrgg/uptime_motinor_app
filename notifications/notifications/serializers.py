from rest_framework import serializers
from .models import Notifications


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = [
            "id",
            "user_id",
            "receiver_type",
            "type",
            'title',
            'message',
            'is_sent',
            "created_at",
        ]
        read_only_fields = ["id", "user_id", "created_at"]
