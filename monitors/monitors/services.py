import time
import httpx
from .models import Monitor, CheckResult


async def execute_monitor_check(monitor: Monitor) -> CheckResult:
    """
    Выполняет HTTP-запрос к URL монитора и возвращает готовый CheckResult.
    """
    start_time = time.perf_counter()

    status_code = None
    is_success = False
    error_message = None

    # Настройки таймаута: 10 секунд на соединение и чтение
    timeout = httpx.Timeout(10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.request(
                method=monitor.method,
                url=monitor.url,
            )

            status_code = response.status_code

            # Проверка статуса
            status_matches = status_code == monitor.expected_status_code

            # Проверка наличия ключевого слова в ответе (если задано)
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
        error_message = f"[execute_monitor_check] Неизвестная ошибка: {str(exc)}"

    # Считаем время выполнения в миллисекундах
    response_time_ms = int((time.perf_counter() - start_time) * 1000)

    return CheckResult(
        monitor=monitor,
        status_code=status_code,
        response_time_ms=response_time_ms,
        is_success=is_success,
        error_message=error_message,
    )
