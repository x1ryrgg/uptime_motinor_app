import logging
import sys
import structlog


def setup_logging(service_name: str, log_level: str = "INFO"):
    """
    Единая точка настройки логирования для всех микросервисов.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # Пробрасывает correlation_id из async-контекста
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),  # Вывод строго в JSON
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)