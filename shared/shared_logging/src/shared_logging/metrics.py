import time
from prometheus_client import Counter, Histogram, start_http_server

# 1. Общие метрики для HTTP / gRPC запросов
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["service", "method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "method", "endpoint"],
)

# 2. Специфичная метрика для ваших проверок (Probes)
PROBE_CHECKS_TOTAL = Counter(
    "probe_checks_total",
    "Total number of probe execution checks",
    ["service", "probe_id", "is_success"],
)

PROBE_CHECK_DURATION = Histogram(
    "probe_check_duration_seconds",
    "Probe execution duration in seconds",
    ["service", "probe_id"],
)


def start_metrics_server(port: int = 8000):
    """
    Запускает фоновый HTTP-сервер Prometheus для фоновых сервисов и gRPC
    (у которых нет собственного HTTP-фреймворка, например FastAPI/Django).
    """
    start_http_server(port)