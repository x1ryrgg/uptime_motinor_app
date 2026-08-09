import os
import sys
import logging
from concurrent import futures
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grpc_server")

PORT = os.getenv("PROBE_GRPC_PORT", "50051")

def serve():
    # Создаем gRPC сервер с пулом воркеров (потоков)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Регистрируем наш сервис
    users_pb2_grpc.add_UserServiceServicer_to_server(
        UserGrpcService(), server
    )

    server.add_insecure_port(f"[::]:{PORT}")
    server.start()
    logger.info(f"🚀 gRPC Server запущен и слушает порт {PORT}...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Остановка gRPC сервера...")
        server.stop(0)


if __name__ == "__main__":
    serve()