import logging
import grpc
from user_support.models import User, UserSettings

from proto import users_pb2_grpc, users_pb2

logger = logging.getLogger("user_support")


class UserGrpcService(users_pb2_grpc.UserServiceServicer):
    """ Реализация gRPC-сервиса для получения контактов пользователя """

    def GetUserNotificationSettings(self, request, context):
        user_id = request.user_id
        logger.info(f"[gRPC] Получен запрос настроек для user_id={user_id}")

        try:
            user = User.objects.get(id=user_id)
            # Получаем настройки (или создаем дефолтные, если их вдруг нет)
            settings, _ = UserSettings.objects.get_or_create(user=user)

            return users_pb2.UserSettingsResponse(
                user_id=user.pk,
                email=user.email or "",
                telegram_chat_id=user.telegram_chat_id or "",
                phone_number=user.phone_number or "",
                email_enabled=settings.email_notification_enabled,
                telegram_enabled=settings.telegram_notification_enabled,
                sms_enabled=settings.sms_notification_enabled,
            )

        except User.DoesNotExist:
            logger.warning(f"[gRPC] Пользователь #{user_id} не найден в БД")
            # Можно вернуть пустые значения
            return users_pb2.UserSettingsResponse(
                user_id=user_id,
                email="",
                telegram_chat_id="",
                phone_number="",
                email_enabled=False,
                telegram_enabled=False,
                sms_enabled=False,
            )
        except Exception as e:
            logger.error(f"[gRPC] Ошибка обработки запроса для user_id={user_id}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return users_pb2.UserSettingsResponse()