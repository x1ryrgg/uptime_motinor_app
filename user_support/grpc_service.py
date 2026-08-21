import grpc
from shared_logging.logging import get_logger
from user_support.models import User, UserSettings

from proto import users_pb2_grpc, users_pb2

logger = get_logger(__name__)


class UserGrpcService(users_pb2_grpc.UserServiceServicer):
    """ Реализация gRPC-сервиса для получения контактов пользователя """

    def GetUserNotificationSettings(self, request, context):
        user_id = request.user_id
        logger.info(
            "Executing user check",
            user_id=user_id,
        )

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
            logger.warning(
                "User does not exist",
                user_id=user_id
            )
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
        except Exception as exc:
            logger.error(
                "GetUserNotificationSettings internal error",
                user_id=user_id,
                exc_info=True,
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return users_pb2.UserSettingsResponse()