import time
import logging

logger = logging.getLogger('incidents.middleware')

class LoggerMiddleware:
    """
    Middleware для логирования входящих HTTP-запросов и ответов API.
    Фиксирует метод, URL, статус ответа и время выполнения задержки.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        # Получаем IP-адрес клиента
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Лог входного запроса
        logger.info(f"---> [START] {request.method} {request.path} | IP: {ip} | User: {request.user}")

        response = self.get_response(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        log_message = (
            f"<--- [END] {request.method} {request.path} | "
            f"Status: {response.status_code} | Duration: {duration_ms}ms"
        )

        if response.status_code >= 500:
            logger.error(log_message)
        elif response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return response

    def process_exception(self, request, exception):
        """Логирование необработанных исключений в представлениях"""
        logger.exception(f"❌ [EXCEPTION] {request.method} {request.path}: {exception}")
        return None