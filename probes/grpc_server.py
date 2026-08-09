import asyncio
import os
import sys
import logging
import grpc
from dotenv import load_dotenv

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("probes.server")

PORT = os.getenv("PROBE_GRPC_PORT", "50052")


async def serve():
    server = grpc.aio.server()

    # Регистрируем сервис
    probes_pb2_grpc.add_ProbeServiceServicer_to_server(
        ProbeGrpcService(), server
    )

    listen_addr = f"[::]:{PORT}"
    server.add_insecure_port(listen_addr)

    logger.info(f"🚀 Probes gRPC Async Server запущен на {listen_addr}...")
    await server.start()

    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("Остановка gRPC сервера...")
        await server.stop(0)


if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен комбинацией Ctrl+C")