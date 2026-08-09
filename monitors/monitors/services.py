import time
import httpx
import logging
from monitors.models import Monitor, CheckResult
from monitors.grpc_client import execute_probe_check_via_grpc

logger = logging.getLogger("monitors")


async def execute_monitor_check_local(monitor: Monitor) -> CheckResult:
    """
    Резервная (Fallback) функция: выполняет HTTP-запрос напрямую из monitors.
    Вызывается, если gRPC сервис probes недоступен.
    """
    start_time = time.perf_counter()
    status_code = None
    is_success = False
    error_message = None
    timeout = httpx.Timeout(10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.request(
                method=monitor.method,
                url=monitor.url,
            )

            status_code = response.status_code

            status_matches = status_code == monitor.expected_status_code

            keyword_matches = True
            if monitor.expected_keyword:
                keyword_matches = monitor.expected_keyword in response.text

            is_success = status_matches and keyword_matches

            if not status_matches:
                error_message = f"Ожидался статус {monitor.expected_status_code}, получен {status_code}"
            elif not keyword_matches:
                error_message = (
                    f"Ключевое слово '{monitor.expected_keyword}' не найдено в ответе"
                )

    except httpx.TimeoutException:
        error_message = "Таймаут соединения (превышено 10 сек)"
    except httpx.RequestError as exc:
        error_message = f"Ошибка сети: {str(exc)}"
    except Exception as exc:
        error_message = f"[Local Check Error] Неизвестная ошибка: {str(exc)}"

    response_time_ms = int((time.perf_counter() - start_time) * 1000)

    return CheckResult(
        monitor=monitor,
        status_code=status_code,
        response_time_ms=response_time_ms,
        is_success=is_success,
        error_message=error_message,
    )


async def execute_monitor_check(monitor: Monitor) -> CheckResult:
    """
    Главная функция проверки:
    1. Пробует сделать запрос через gRPC сервис probes.
    2. Если probes недоступен/упал, переключается на локальный HTTP-запрос (Fallback).
    """
    try:
        probe_response = await execute_probe_check_via_grpc(
            monitor_id=monitor.pk,
            url=monitor.url,
            method=monitor.method,
            expected_status_code=monitor.expected_status_code,
            expected_keyword=monitor.expected_keyword,
            timeout_seconds=10.0,
        )

        # Если gRPC вернул корректный словарь
        if probe_response is not None:
            return CheckResult(
                monitor=monitor,
                status_code=probe_response["status_code"] if probe_response["status_code"] != 0 else None,
                response_time_ms=probe_response["response_time_ms"],
                is_success=probe_response["is_success"],
                error_message=probe_response["error_message"] or None,
            )
    except Exception as exc:
        logger.error(f"[gRPC Fail] Ошибка при обращении к probes: {exc}")

        # Fallback: если gRPC вернул None или выбросил исключение
    logger.warning(
        f"⚠️ [Fallback Triggered] Сервис probes недоступен для монитора #{monitor.pk}. "
        f"Выполняется локальная проверка из monitors..."
    )
    return await execute_monitor_check_local(monitor)