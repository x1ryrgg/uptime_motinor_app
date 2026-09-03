# Deployment

**Инструкция по локальному развёртыванию UptimeMonitor с использованием Kubernetes
и Docker Compose.**

---

# Поднятие Kubernetes

### Требования
- Docker Desktop
- Kubernetes включён в Docker Desktop
- kubectl
- Git

---

**Проверка Kubernetes:**

```bash
kubectl version --client
kubectl get nodes
```

## Подготовка secrets:

**config/common-secret.yaml**
```dotenv
apiVersion: v1
kind: Secret
metadata:
  name: common-secret
  namespace: uptime-monitor
type: Opaque
stringData:
  SECRET_KEY: "" 
  DB_PASSWORD: ""
```

**config/incidents&monitors-secret.yaml**
```dotenv
apiVersion: v1
kind: Secret
metadata:
  name: incidents-secret / monitors-secret
  namespace: uptime-monitor
type: Opaque
stringData: {}
```

**config/notifications-secret.yaml**
```dotenv
apiVersion: v1
kind: Secret
metadata:
  name: notifications-secret
  namespace: uptime-monitor
type: Opaque
stringData:
  EMAIL_HOST_PASSWORD: ""
  TELEGRAM_BOT_TOKEN: ""
```

**config/user-support-secret.yaml**
```dotenv
apiVersion: v1
kind: Secret
metadata:
  name: user-support-secret
  namespace: uptime-monitor
type: Opaque
stringData:
  GITHUB_CLIENT_ID: ""
  GITHUB_CLIENT_SECRET: ""
```

**postgres/secret.yaml**
```dotenv
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: uptime-monitor
type: Opaque
stringData:
  POSTGRES_USER: ""
  POSTGRES_PASSWORD: ""
  POSTGRES_DB: "uptimemonitor"
```

**rabbitmq/secret.yaml**
```dotenv
apiVersion: v1
kind: Secret
metadata:
  name: rabbitmq-secret
  namespace: uptime-monitor
type: Opaque
stringData:
  RABBITMQ_DEFAULT_USER: "guest"
  RABBITMQ_DEFAULT_PASS: "guest"
```

---

## Разворачивание сервиса

**Создание namespace**
```bash
kubectl apply -f k8s/namespace.yaml
```

**Создание конфигурации**
```bash
kubectl apply -f k8s/config/
```

**PostgreSQL**
```bash
kubectl apply -f k8s/postgres/
```

Redis**
```bash
kubectl apply -f k8s/redis/
```

**RabbitMQ**
```bash
kubectl apply -f k8s/rabbitmq/
```

**Probes**
```bash
kubectl apply -f k8s/probes/
```

**User Support**
```bash
kubectl apply -f k8s/user-support/
```

**Monitors**
```bash
kubectl apply -f k8s/monitors/
```

**Incidents**
```bash
kubectl apply -f k8s/incidents/
```

**Notifications**
```bash
kubectl apply -f k8s/notifications/
```

**Nginx**
```bash
kubectl apply -f k8s/nginx/
```

---

## Проверка deployment

**Все Pod:**
```bash
kubectl get pods -n uptime-monitor
```

**Services:**
```bash
kubectl get svc -n uptime-monitor
```

**Deployment:**
```bash
kubectl get deployments -n uptime-monitor
```

**Все ресурсы namespace:**
```bash
kubectl get all -n uptime-monitor
```

**Логи конкретного Pod:**
```bash
kubectl logs -n uptime-monitor <pod-name>
```

**Следить за логами в реальном времени:**
```bash
kubectl logs -f -n uptime-monitor deploy/monitors-worker
```

---

## Database migrations

После первого запуска необходимо выполнить Django migrations.

**user_support**
```bash
kubectl apply -f k8s/user-support/migration-job.yaml
```

**monitors**
```bash
kubectl apply -f k8s/monitors/migration-job.yaml
```

**incidents**
```bash
kubectl apply -f k8s/incidents/migration-job.yaml
```

**notifications**
```bash
kubectl apply -f k8s/notifications/migration-job.yaml
```

---

# Docker Compose

## Пример общего .env
```dotenv
POSTGRES_DB=uptimemonitor
POSTGRES_USER=something
POSTGRES_PASSWORD=something
POSTGRES_PORT=5432

RABBITMQ_DEFAULT_USER=something
RABBITMQ_DEFAULT_PASS=something
RABBITMQ_PORT=5672
RABBITMQ_MGMT_PORT=15672

REDIS_PORT=6379

PROMETHEUS_PORT=9090
LOKI_PORT=3100
GRAFANA_PORT=3000

NGINX_PORT=80

USER_SUPPORT_GRPC_PORT=50051
USER_SUPPORT_GRPC_HOST=user_support_grpc:50051
PROBES_GRPC_HOST=probes_grpc:50052
```

## Общие настройки в каждом сервисе

#### Настройки необходимы для сервисов: user_support, monitors, incidents и notifications

#### Важно, чтобы SECRET_KEY между сервисами был одинаковый для работы jwt auth

```dotenv
SECRET_KEY='...'
DEBUG=True

DJANGO_ALLOWED_HOSTS=<service_name>.localhost,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://<service_name>.localhost

DB_NAME=uptimer_<service_name>
```

## Специфичные environments сервисов

**user_support**
```dotenv
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

**monitors**
```dotenv
nothing
```

**incidents**
```dotenv
nothing
```

**notifications**
```dotenv
EMAIL_HOST='...'
EMAIL_PORT=...
EMAIL_USE_SSL=True
EMAIL_USE_TLS=False
EMAIL_HOST_USER='...'
EMAIL_HOST_PASSWORD=...

TELEGRAM_BOT_TOKEN=...
```

## Команды работы с docker compose

**Запуск создания контейнера:**
```bash
docker compose up --build -d
```

**Остановка:**
```bash
docker compose down
```













