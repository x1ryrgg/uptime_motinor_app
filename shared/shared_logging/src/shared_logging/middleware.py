import uuid
import structlog

logger = structlog.get_logger("django_http_middleware")


class SharedLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Извлекаем или генерируем X-Request-ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 2. Привязываем контекст (request_id, path, method) ко ВСЕМ логам текущего запроса
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.path,
            method=request.method,
        )

        response = self.get_response(request)

        # 3. Проставляем заголовок в ответ клиенту
        response["X-Request-ID"] = request_id

        # 4. Логируем завершение запроса
        logger.info(
            "HTTP Request processed",
            status_code=response.status_code,
            path=request.path,
            method=request.method,
        )

        return response