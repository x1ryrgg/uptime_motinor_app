import os
import sys
import logging
import grpc
from shared_logging.logging import get_logger
from dotenv import load_dotenv

load_dotenv()

# 1. Прокидываем путь к папке proto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Если файл в подпапке (например, monitors/grpc_client.py):
PROJECT_DIR = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == "monitors" else BASE_DIR
PROTO_DIR = os.path.join(PROJECT_DIR, "proto")

if PROTO_DIR not in sys.path:
    sys.path.append(PROTO_DIR)

import probes_pb2
import probes_pb2_grpc


logger = get_logger(__name__)

# Хост и порт gRPC-сервера probes
PROBES_GRPC_HOST = os.getenv("PROBES_GRPC_HOST", )


async def execute_probe_check_via_grpc(
    monitor_id: int,
    url: str,
    method: str = "GET",
    expected_status_code: int = 200,
    expected_keyword: str | None = None,
    timeout_seconds: float = 10.0,
) -> dict | None:
    """
    Выполняет асинхронный gRPC-запрос в сервис probes для сетевой проверки.
    """

    logger.debug(
        "Sending gRPC check request to probes",
        monitor_id=monitor_id,
        url=url,
        grpc_host=PROBES_GRPC_HOST,
    )

    try:
        # Используем асинхронный gRPC канал
        async with grpc.aio.insecure_channel(PROBES_GRPC_HOST) as channel:
            stub = probes_pb2_grpc.ProbeServiceStub(channel)

            request = probes_pb2.ProbeCheckRequest(
                monitor_id=monitor_id,
                url=url,
                method=method,
                expected_status_code=expected_status_code,
                expected_keyword=expected_keyword,
                timeout_seconds=timeout_seconds,
            )

            # Вызываем асинхронный RPC метод с таймаутом ожидания ответа
            response = await stub.ExecuteCheck(request, timeout=timeout_seconds + 2.0)

            logger.info(
                "gRPC check response received",
                monitor_id=monitor_id,
                is_success=response.is_success,
                response_time_ms=response.response_time_ms,
                probe_id=response.probe_id,
            )

            return {
                "status_code": response.status_code,
                "response_time_ms": response.response_time_ms,
                "is_success": response.is_success,
                "error_message": response.error_message,
                "probe_id": response.probe_id,
            }

    except grpc.RpcError as e:
        logger.error(
            "gRPC probe execution failed",
            monitor_id=monitor_id,
            grpc_code=e.code().name if e.code() else "UNKNOWN",
            grpc_details=e.details(),
            grpc_host=PROBES_GRPC_HOST,
        )
        return None
    except Exception as e:
        logger.error(
            "Unexpected error during gRPC probe execution",
            monitor_id=monitor_id,
            grpc_host=PROBES_GRPC_HOST,
            exc_info=True,
        )
        return None