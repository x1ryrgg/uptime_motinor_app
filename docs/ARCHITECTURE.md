# UptimeMonitor — Architecture

## 1. Overview

**UptimeMonitor** — асинхронная микросервисная платформа для мониторинга доступности веб-ресурсов по HTTP/HTTPS.

Система выполняет периодические проверки целевых ресурсов, определяет сбои и восстановления, регистрирует инциденты и отправляет уведомления пользователям через внешние каналы.

Проект построен на следующих архитектурных принципах:

- Microservices Architecture
- Event-Driven Architecture (EDA)
- Database per Service
- Asynchronous Processing
- gRPC для внутренних RPC-вызовов
- RabbitMQ для обмена событиями
- Redis для Celery
- Docker для контейнеризации
- Kubernetes для оркестрации
- Prometheus + Grafana для мониторинга
- Loki для централизованного хранения логов

---

# 2. High-Level Architecture

```mermaid
flowchart TB

    Client["Client / SPA / Mobile / Postman"]

    subgraph K8S["Kubernetes Cluster"]

        subgraph API["API Layer"]

            US["user-support-web<br/>HTTP :8000"]
            MON["monitors-web<br/>HTTP :8000"]
            INC["incidents-web<br/>HTTP :8000"]
            NOT["notifications-web<br/>HTTP :8000"]

        end

        subgraph WORKERS["Background Workers"]

            MB["monitors-beat"]
            MW["monitors-worker"]

            IW["incidents-worker"]

            NW["notifications-worker"]
        end

        subgraph GRPC["gRPC Services"]

            USG["user-support-grpc<br/>:50051"]
            PROBES["probes<br/>:50052"]
        end

        subgraph INFRA["Infrastructure"]

            RABBIT["RabbitMQ<br/>:5672"]
            REDIS["Redis<br/>:6379"]
            PG["PostgreSQL<br/>:5432"]
        end

        subgraph OBS["Observability"]

            PROM["Prometheus<br/>:9090"]
            LOKI["Loki<br/>:3100"]
            GRAFANA["Grafana<br/>:3000"]
        end

    end

    Client --> US
    Client --> MON
    Client --> INC
    Client --> NOT

    US --> PG
    MON --> PG
    INC --> PG
    NOT --> PG

    USG --> PG

    MB --> RABBIT
    RABBIT --> MW

    MW --> PROBES
    PROBES --> External["External Websites"]

    MW --> RABBIT
    RABBIT --> IW

    IW --> USG
    IW --> RABBIT

    RABBIT --> NW
    NW --> ExternalProviders["Telegram / Email / SMS"]

    MW --> REDIS
    IW --> REDIS
    NW --> REDIS

    PROM --> US
    PROM --> MON
    PROM --> INC
    PROM --> NOT

    GRAFANA --> PROM
    GRAFANA --> LOKI