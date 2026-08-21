import os
import sys
import grpc
from shared_logging.logging import get_logger
from dotenv import load_dotenv

load_dotenv()

# 1. Динамически находим папку proto относительно текущего файла и добавляем в sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # .../incidents/incidents
PROJECT_DIR = os.path.dirname(CURRENT_DIR)                 # .../incidents
PROTO_DIR = os.path.join(PROJECT_DIR, "proto")            # .../incidents/proto

if PROTO_DIR not in sys.path:
    sys.path.append(PROTO_DIR)

# 2. Прямые импорты (теперь import users_pb2 внутри users_pb2_grpc отработает
import users_pb2
import users_pb2_grpc

logger = get_logger(__name__)

# Адрес и порт запущенного gRPC-сервера user_support
USER_SUPPORT_GRPC_HOST = os.getenv("USER_SUPPORT_GRPC_HOST")


def get_user_settings_via_grpc(user_id: int) -> dict | None:
    """Делает синхронный gRPC-запрос в сервис user_support для получения контактов"""
    try:
        # Открываем канал связи с сервером
        with grpc.insecure_channel(USER_SUPPORT_GRPC_HOST) as channel:
            stub = users_pb2_grpc.UserServiceStub(channel)

            # Формируем запрос
            request = users_pb2.UserRequest(user_id=user_id)

            # Вызываем удаленный метод (RPC)
            response = stub.GetUserNotificationSettings(request, timeout=3.0)

            logger.info(
                "gRPC check response success",
                user_id=user_id,
            )

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
        logger.error(
            "gRPC user_support execution failed",
            user_id=user_id,
            grpc_code=e.code().name if e.code() else "UNKNOWN",
            grpc_details=e.details(),
            grpc_host=USER_SUPPORT_GRPC_HOST,
        )
        return None
    except Exception as e:
        logger.error(
            "Unexpected error during gRPC probe execution",
            user_id=user_id,
            grpc_host=USER_SUPPORT_GRPC_HOST,
            exc_info=True,
        )
        return None