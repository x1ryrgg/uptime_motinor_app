import time
import httpx
import logging

logger = logging.getLogger(__name__)


# Глобальный клиент (Singleton) с ограниченным пулом и отключенной верификацией SSL
http_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=10000,          # Макс. параллельных сокетов на процесс
        max_keepalive_connections=2000, # Сохраняем горячие соединения
    ),
    follow_redirects=True,
)

async def execute_http_check(
    url: str,
    method: str = "GET",
    expected_status_code: int = 200,
    expected_keyword: str | None = None,
    timeout_seconds: float = 10.0,
) -> dict:
    """
    Выполняет асинхронный HTTP/HTTPS запрос и возвращает метрики.
    """
    start_time = time.perf_counter()

    status_code = 0
    is_success = False
    error_message = ""

    # Настройки таймаута для httpx
    timeout = httpx.Timeout(timeout_seconds)

    try:
        response = await http_client.request(
            method=method.upper(),
            url=url,
            timeout=timeout,
        )

        status_code = response.status_code

        # Валидация статус-кода
        status_matches = status_code == expected_status_code

        # Валидация ключевого слова (если передано)
        keyword_matches = True
        if expected_keyword:
            keyword_matches = expected_keyword in response.text

        is_success = status_matches and keyword_matches

        if not status_matches:
            error_message = (
                f"[execute_http_check] Ожидался статус {expected_status_code}, получен {status_code}"
            )
        elif not keyword_matches:
            error_message = (
                f"[execute_http_check] Ключевое слово '{expected_keyword}' не найдено в ответе"
            )

    except httpx.TimeoutException:
        error_message = f"[execute_http_check] Таймаут соединения (превышено {timeout_seconds} сек)"
    except httpx.RequestError as exc:
        error_message = f"[execute_http_check] Ошибка сети: {str(exc)}"
    except Exception as exc:
        error_message = f"[execute_http_check] Неизвестная ошибка: {str(exc)}"

    response_time_ms = int((time.perf_counter() - start_time) * 1000)

    return {
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "is_success": is_success,
        "error_message": error_message,
    }