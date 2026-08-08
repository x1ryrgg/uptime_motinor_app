# 🚀 UptimeMonitor

**UptimeMonitor** — асинхронная микросервисная платформа для непрерывного мониторинга доступности веб-ресурсов (HTTP/HTTPS) с автоматической регистрацией инцидентов и мгновенным уведомлением пользователей через Telegram, Email и SMS.

---

## 🛠 Технологический стек

* **Language:** Python 3.13
* **Frameworks & Core:** Django, Django REST Framework, gRPC (Protobuf)
* **Dependency Management:** Poetry
* **Async & Task Management:** Celery, Celery Beat
* **Message Broker:** RabbitMQ
* **Databases & Cache:** PostgreSQL (отдельная БД для каждого сервиса), Redis
* **Auth:** JWT (JSON Web Tokens), OAuth 
* **DevOps & Containerization:** Docker, Docker Compose

---

## 🏗 Архитектура и микросервисы

Проект построен по принципам событийно-ориентированной микросервисной архитектуры (EDA) с полным разделением баз данных (**Database per Service**).

```mermaid
graph TD
    classDef clientStyle fill:#0d0e12,stroke:#4a5568,stroke-width:2px,color:#f8fafc;
    classDef serviceStyle fill:#16192b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;
    classDef dbStyle fill:#0f172a,stroke:#0ea5e9,stroke-width:2px,color:#f8fafc;
    classDef brokerStyle fill:#1e1029,stroke:#a855f7,stroke-width:2px,color:#f8fafc;

    subgraph ClientLayer ["Client / External API"]
        Client["SPA / Mobile / Postman<br/>(JWT Authentication)/OAuth"]:::clientStyle
    end

    subgraph Microservices ["Microservices Layer (Django / DRF)"]
        subgraph UserSupportGroup ["user_support"]
            US_WEB["user_support_web<br/>:8001 (Auth & Users)"]:::serviceStyle
            US_GRPC["user_support_grpc<br/>:50051 (gRPC Server)"]:::serviceStyle
        end

        subgraph MonitorsGroup ["monitors"]
            M_WEB["monitors_web<br/>:8002 (CRUD Monitors)"]:::serviceStyle
            M_BEAT["monitors_beat<br/>(Periodic Schedule)"]:::serviceStyle
            M_WORKER["monitors_worker<br/>(HTTP Check Tasks)"]:::serviceStyle
        end

        subgraph IncidentsGroup ["incidents"]
            INC_WEB["incidents_web<br/>:8003 (Incidents API)"]:::serviceStyle
            INC_WORKER["incidents_worker<br/>(Incident Consumer)"]:::serviceStyle
        end

        subgraph NotificationsGroup ["notifications"]
            NOTIF_WEB["notifications_web<br/>:8004 (History API)"]:::serviceStyle
            NOTIF_WORKER["notifications_worker<br/>(Email/TG/SMS Sender)"]:::serviceStyle
        end
    end

    subgraph EventBackbone ["Message Broker & Cache"]
        RabbitMQ[("RabbitMQ<br/>:5672 / :15672<br/>(Exchanges & Queues)")]:::brokerStyle
        Redis[("Redis<br/>:6379<br/>(Celery Backend / Cache)")]:::brokerStyle
    end

    subgraph Persistence ["Persistence Layer (PostgreSQL Container :5432)"]
        DB_USERS[("DB: uptimer_users")]:::dbStyle
        DB_MONITORS[("DB: uptimer_monitors")]:::dbStyle
        DB_INCIDENTS[("DB: uptimer_incidents")]:::dbStyle
        DB_NOTIFICATIONS[("DB: uptimer_notifications")]:::dbStyle
    end

    Client -->|"1. Auth / Login (JWT)"| US_WEB
    Client -->|"2. Create Monitors / Rules"| M_WEB
    Client -->|"View Incidents"| INC_WEB

    US_WEB --- DB_USERS
    US_GRPC --- DB_USERS
    M_WEB --- DB_MONITORS
    M_WORKER --- DB_MONITORS
    INC_WORKER --- DB_INCIDENTS
    INC_WEB --- DB_INCIDENTS
    NOTIF_WORKER --- DB_NOTIFICATIONS
    NOTIF_WEB --- DB_NOTIFICATIONS

    M_BEAT -->|"Trigger Checks"| RabbitMQ
    RabbitMQ -->|"Fetch Task"| M_WORKER
    M_WORKER -->|"Result / Latency"| Redis

    M_WORKER -->|"Publish Failure/Recovery Event"| RabbitMQ
    RabbitMQ -->|"incidents_queue"| INC_WORKER
    INC_WORKER -->|"Publish Notification Event"| RabbitMQ
    RabbitMQ -->|"notifications_queue"| NOTIF_WORKER

    INC_WORKER ==>|"gRPC: Get User Contacts<br/>(User Support Proto)"| US_GRPC
    NOTIF_WORKER -->|"Send Alert"| External[("External Providers<br/>Telegram / Email / SMS")]:::clientStyle
```


### Разделение по сервисам

* **`user_support`**
  * Управление пользователями, аутентификация и авторизация (JWT).
  * Предоставляет **gRPC-сервер** (`grpc_server.py`) для быстрого синхронного получения данных пользователей другими микросервисами без нагрузки на REST API.

* **`monitors`**
  * Настройка таргетов (URL, интервалы проверки, ожидаемые статусы).
  * **Celery Beat** планирует периодические таски, пингует сайты, фиксирует время отклика и отправляет результаты в RabbitMQ.

* **`incidents`**
  * Обрабатывает события из RabbitMQ.
  * Фиксирует падения/восстановления сайтов, формирует инциденты и историю даунтайма.
  * При необходимости запрашивает данные владельца через **gRPC Client** в `user_support`.

* **`notifications`**
  * Сервис доставки сообщений (Email, Telegram, SMS).
  * Читает события из `notifications_queue` и отправляет асинхронные уведомления пользователям при смене статуса их сайтов (при первом падении или восстановлении).

---

## 🔄 Основной бизнес-процесс (Flow данных)

1. **Инициализация:** Celery Beat внутри сервиса `monitors` по расписанию триггерит проверку списка сайтов.
2. **Пинг:** Рабочие воркеры совершают HTTP-запросы к целевым ресурсам и фиксируют метрики (`latency`, `status code`, `availability`).
3. **Обработка события:** Результат проверки отправляется в брокер сообщений **RabbitMQ**.
4. **Регистрация инцидента:** Сервис `incidents` вычитывает событие. Если сайт упал (или восстановился после сбоя), создается или закрывается объект инцидента.
5. **gRPC-интеграция:** Сервис `incidents` делает межсервисный gRPC-вызов к `user_support` для получения контактов владельца ресурса.
6. **Уведомление:** Сообщение о сбое или восстановлении отправляется в очередь `notifications`, откуда воркеры нотификаций отправляют сообщения в Telegram / Email / SMS.

---

## 📁 Структура проекта

```text
uptimemonitor/
├── user_support/           # Микросервис пользователей & gRPC Server
│   ├── config/              # Настройка сервиса
│   ├── proto/              # Protobuf контракты (.proto)
│   ├── grpc_server.py      # Запуск gRPC сервера
│   └── user_support/       # Django app
├── monitors/               # Микросервис проверки сайтов & Celery Beat
│   ├── config/              # Настройка сервиса
│   └── monitors/           # Django app & tasks
├── incidents/              # Микросервис регистрации сбоев & gRPC Client
│   ├── config/              # Настройка сервиса
│   ├── proto/              # Protobuf контракты для обращения к user_support
│   └── incidents/          # Django app & tasks
├── notifications/          # Микросервис отправки сообщений (Email/TG/SMS)
│   ├── config/              # Настройка сервиса
│   └── notifications/      # Django app & tasks
├── init-multiple-dbs.sql   # Скрипт инициализации независимых БД в PostgreSQL
├── docker-compose.yml      # Локальный запуск всего окружения
└── README.md