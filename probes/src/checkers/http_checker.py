import time
import httpx
import logging
from abc import ABC, abstractmethod
from .dataclasses import HttpCheckParams, CheckResult

logger = logging.getLogger(__name__)


class BaseChecker(ABC):
    @abstractmethod
    async def execute(self, params: HttpCheckParams) -> CheckResult:
        """Выполняет проверку доступности ресурса."""
        pass


class HttpChecker(BaseChecker):
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def execute(self, params: HttpCheckParams) -> CheckResult:
        start_time = time.perf_counter()

        try:
            response = await self._client.request(
                method=params.method.upper(),
                url=params.url,
                timeout=httpx.Timeout(params.timeout_seconds),
            )

            is_success, error_msg = self._validate_response(response, params)
            return self._build_result(response.status_code, start_time, is_success, error_msg)

        except httpx.TimeoutException:
            return self._build_result(0, start_time, False, f"[HttpChecker] Таймаут ({params.timeout_seconds}s)")
        except httpx.RequestError as exc:
            return self._build_result(0, start_time, False, f"[HttpChecker] Ошибка сети: {exc}")
        except Exception as exc:
            return self._build_result(0, start_time, False, f"[HttpChecker] Неизвестная ошибка: {exc}")

    def _validate_response(self, response: httpx.Response, params: HttpCheckParams) -> tuple[bool, str]:
        if response.status_code != params.expected_status_code:
            return False, f"[HttpChecker] Ожидался статус {params.expected_status_code}, получен {response.status_code}"
        if params.expected_keyword and params.expected_keyword not in response.text:
            return False, f"[HttpChecker] Ключевое слово '{params.expected_keyword}' не найдено в ответе"
        return True, ""

    def _build_result(self, status_code: int, start_time: float, is_success: bool, error_message: str) -> CheckResult:
        response_time_ms = int((time.perf_counter() - start_time) * 1000)
        return CheckResult(
            status_code=status_code,
            response_time_ms=response_time_ms,
            is_success=is_success,
            error_message=error_message,
        )

# async def execute_http_check(
#     url: str,
#     method: str = "GET",
#     expected_status_code: int = 200,
#     expected_keyword: str | None = None,
#     timeout_seconds: float = 10.0,
# ) -> dict:
#     """
#     Выполняет асинхронный HTTP/HTTPS запрос и возвращает метрики.
#     """
#     start_time = time.perf_counter()
#
#     status_code = 0
#     is_success = False
#     error_message = ""
#
#     # Настройки таймаута для httpx
#     timeout = httpx.Timeout(timeout_seconds)
#
#     try:
#         response = await http_client.request(
#             method=method.upper(),
#             url=url,
#             timeout=timeout,
#         )
#
#         status_code = response.status_code
#
#         # Валидация статус-кода
#         status_matches = status_code == expected_status_code
#
#         # Валидация ключевого слова (если передано)
#         keyword_matches = True
#         if expected_keyword:
#             keyword_matches = expected_keyword in response.text
#
#         is_success = status_matches and keyword_matches
#
#         if not status_matches:
#             error_message = (
#                 f"[execute_http_check] Ожидался статус {expected_status_code}, получен {status_code}"
#             )
#         elif not keyword_matches:
#             error_message = (
#                 f"[execute_http_check] Ключевое слово '{expected_keyword}' не найдено в ответе"
#             )
#
#     except httpx.TimeoutException:
#         error_message = f"[execute_http_check] Таймаут соединения (превышено {timeout_seconds} сек)"
#     except httpx.RequestError as exc:
#         error_message = f"[execute_http_check] Ошибка сети: {str(exc)}"
#     except Exception as exc:
#         error_message = f"[execute_http_check] Неизвестная ошибка: {str(exc)}"
#
#     response_time_ms = int((time.perf_counter() - start_time) * 1000)
#
#     return {
#         "status_code": status_code,
#         "response_time_ms": response_time_ms,
#         "is_success": is_success,
#         "error_message": error_message,
#     }