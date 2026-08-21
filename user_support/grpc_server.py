import os
import sys
from concurrent import futures
from shared_logging.logging import get_logger
import grpc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROTO_DIR = os.path.join(BASE_DIR, "proto")

# Добавляем папку proto в sys.path
if PROTO_DIR not in sys.path:
    sys.path.append(PROTO_DIR)

# Инициализация Django ORM перед запуском сервера
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

# Прямые импорты после добавления в sys.path и настройки Django
import users_pb2_grpc
from grpc_service import UserGrpcService


logger = get_logger(__name__)

PORT = os.getenv("USER_SUPPORT_GRPC_PORT", "50051")

def serve():
    # Создаем gRPC сервер с пулом воркеров (потоков)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Регистрируем наш сервис
    users_pb2_grpc.add_UserServiceServicer_to_server(
        UserGrpcService(), server
    )

    listen_addr = f"[::]:{PORT}"
    server.add_insecure_port(listen_addr)
    server.start()

    logger.info("gRPC Server started successfully", port=PORT, listen_addr=listen_addr)

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Stopping gRPC server gracefully...")
        # Даем 5 секунд на завершение текущих gRPC-запросов
        server.stop(grace=5)
    except Exception:
        logger.error("gRPC server crashed unexpectedly", exc_info=True)
        server.stop(grace=0)


if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")