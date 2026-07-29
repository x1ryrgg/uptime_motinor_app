from django.contrib.sessions import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework import serializers

from user_support.models import User, UserSettings


class UserSerializer(serializers.ModelSerializer):
    confirm_password =  serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "confirm_password", "first_name", "last_name")
        extra_kwargs = {
            'id': {'read_only': True},
            "password": {"write_only": True}
        }

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(**validated_data)
        UserSettings.objects.create(user=user)
        return user
