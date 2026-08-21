FROM python:3.13-slim AS builder

# Настройки Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.2.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

WORKDIR /app

COPY shared /shared

# Копируем зависимости
COPY notifications/pyproject.toml notifications/poetry.lock* ./

# Устанавливаем только продакшен-зависимости
RUN poetry install --no-root --no-interaction

# --- Финальный слой (Production) ---
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Устанавливаем минимальные рантайм-зависимости (включая netcat для wait-for-it проверок)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем виртуальное окружение из builder
COPY --from=builder /app/.venv /app/.venv

COPY --from=builder /shared /shared

COPY notifications/ .
