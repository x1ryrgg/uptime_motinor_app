from django.contrib.sessions import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework import serializers
from django.db import transaction
from .models import User, UserSettings


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
        )
        extra_kwargs = {"id": {"read_only": True}, "password": {"write_only": True}}

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(**validated_data)
        UserSettings.objects.create(user=user)
        return user


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = (
            "id",
            "email_notification_enabled",
            "telegram_notification_enabled",
            "sms_notification_enabled",
        )
        read_only_fields = ("id",)

class PersonalUserSerializer(serializers.ModelSerializer):
    settings = UserSettingsSerializer(required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            'email',
            'phone_number',
            'telegram_chat_id',
            'first_name',
            'last_name',
            'settings',
        )
        read_only_fields = ('id', 'username')

    @transaction.atomic
    def update(self, instance, validated_data):
       settings_data = validated_data.pop("settings", None)

       instance = super().update(instance, validated_data)

       if settings_data is not None:
           # get_or_create обезопасит, если настроек почему-то еще нет в БД
           user_settings, _ = UserSettings.objects.get_or_create(user=instance)

           # Обновляем поля объекта UserSettings
           for attr, value in settings_data.items():
               setattr(user_settings, attr, value)
           user_settings.save()

       return instance

