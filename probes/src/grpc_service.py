import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

# Прокидываем путь к папке proto в sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Папка probes/
PROTO_DIR = os.path.join(BASE_DIR, "proto")
if PROTO_DIR not in sys.path:
    sys.path.append(PROTO_DIR)

import probes_pb2
import probes_pb2_grpc
from src.checkers.http_checker import execute_http_check

logger = logging.getLogger("probes.grpc_service")

# Идентификатор текущей ноды агента (например: fra1, msk1 или default_probe)
PROBE_ID = os.getenv("PROBE_ID", "default_probe")


class ProbeGrpcService(probes_pb2_grpc.ProbeServiceServicer):

    async def ExecuteCheck(
        self, request: probes_pb2.ProbeCheckRequest, context
    ) -> probes_pb2.ProbeCheckResponse:
        logger.info(
            f"[Probe] Выполнение проверки для monitor_id={request.monitor_id} ({request.url})"
        )

        result = await execute_http_check(
            url=request.url,
            method=request.method,
            expected_status_code=request.expected_status_code,
            expected_keyword=request.expected_keyword if request.HasField("expected_keyword") else None,
            timeout_seconds=request.timeout_seconds or 10.0,
        )

        logger.info(
            f"[Probe] Завершена проверка monitor_id={request.monitor_id}. "
            f"Успех: {result['is_success']}, Время: {result['response_time_ms']}ms"
        )

        # Возвращаем Protobuf-ответ
        return probes_pb2.ProbeCheckResponse(
            monitor_id=request.monitor_id,
            status_code=result["status_code"],
            response_time_ms=result["response_time_ms"],
            is_success=result["is_success"],
            error_message=result["error_message"],
            probe_id=PROBE_ID,
        )

