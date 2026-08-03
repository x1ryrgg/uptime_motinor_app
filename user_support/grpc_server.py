# grpc_server.py
import os
import sys
import time
import logging
from concurrent import futures
import grpc

# 1. Инициализация Django ORM перед запуском сервера
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

# 2. Импорты после инициализации Django
from proto import user_support_pb2_grpc
from user_support.grpc_service import UserGrpcService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grpc_server")


def serve():
    # Создаем gRPC сервер с пулом воркеров (потоков)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Регистрируем наш сервис
    user_support_pb2_grpc.add_UserServiceServicer_to_server(
        UserGrpcService(), server
    )

    # Настраиваем порт
    port = "50051"
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"🚀 gRPC Server запущен и слушает порт {port}...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Остановка gRPC сервера...")
        server.stop(0)


if __name__ == "__main__":
    serve()