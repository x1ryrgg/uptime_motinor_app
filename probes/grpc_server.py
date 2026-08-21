import asyncio
import os
import sys
import grpc
import httpx
from dotenv import load_dotenv
from shared_logging.logging import get_logger, setup_logging

load_dotenv()

# Добавляем пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROTO_DIR = os.path.join(BASE_DIR, "proto")

if PROTO_DIR not in sys.path:
    sys.path.append(PROTO_DIR)

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import probes_pb2_grpc
from src.grpc_service import ProbeGrpcService
from src.checkers.http_checker import HttpChecker

logger = get_logger(__name__)

PORT = os.getenv("PROBE_GRPC_PORT", "50052")


async def serve():
    options = [
        ("grpc.max_concurrent_streams", 10000),  # Макс. параллельных стримов/запросов
    ]

    async with httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=10000,
                max_keepalive_connections=2000,
            ),
            follow_redirects=True,
            verify=False,  # Отключение SSL-проверки
    ) as http_client:
        http_checker = HttpChecker(client=http_client)

        # Создаем gRPC сервер
        server = grpc.aio.server(options=options)

        # Регистрируем сервис
        probes_pb2_grpc.add_ProbeServiceServicer_to_server(
            ProbeGrpcService(checker=http_checker),
            server
        )

        listen_addr = f"[::]:{PORT}"
        server.add_insecure_port(listen_addr)

        logger.info("gRPC Server started successfully", port=PORT, listen_addr=listen_addr)
        await server.start()

        try:
            await server.wait_for_termination()
        except KeyboardInterrupt:
            logger.info("Stopping gRPC server gracefully...")
            # Даем 5 секунд на завершение текущих gRPC-запросов
            await server.stop(grace=5)
        except Exception:
            logger.error("gRPC server crashed unexpectedly", exc_info=True)
            await server.stop(grace=0)


if __name__ == "__main__":
    setup_logging(service_name="probes", log_level="INFO")

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")