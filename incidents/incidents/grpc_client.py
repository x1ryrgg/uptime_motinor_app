import logging
import grpc

from proto import user_support_pb2, user_support_pb2_grpc

logger = logging.getLogger("incidents")

# Адрес и порт запущенного gRPC-сервера user_support
USER_SUPPORT_GRPC_HOST = "localhost:50051"


def get_user_settings_via_grpc(user_id: int) -> dict | None:
    """Делает синхронный gRPC-запрос в сервис user_support для получения контактов"""
    try:
        # Открываем канал связи с сервером
        with grpc.insecure_channel(USER_SUPPORT_GRPC_HOST) as channel:
            stub = user_support_pb2_grpc.UserServiceStub(channel)

            # Формируем запрос
            request = user_support_pb2.UserRequest(user_id=user_id)

            # Вызываем удаленный метод (RPC)
            response = stub.GetUserNotificationSettings(request, timeout=3.0)

            logger.info(f"[gRPC Client] Успешно получены данные для user_id={user_id}")

            return {
                "user_id": response.user_id,
                "email": response.email,
                "phone_number": response.phone_number,
                "telegram_chat_id": response.telegram_chat_id,
                "email_enabled": response.email_enabled,
                "telegram_enabled": response.telegram_enabled,
                'sms_enabled': response.sms_enabled,
            }

    except grpc.RpcError as e:
        logger.error(
            f"[gRPC Client Error] Не удалось получить данные пользователя #{user_id}. "
            f"Код: {e.code()}, Детали: {e.details()}"
        )
        return None
    except Exception as e:
        logger.error(f"[gRPC Client Error] Критическая ошибка связи с user_support: {e}")
        return None