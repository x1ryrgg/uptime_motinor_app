# Deployment

Инструкция по локальному развёртыванию UptimeMonitor с использованием Kubernetes
и Docker Compose.

---

# Поднятие Kubernetes

### Требования
- Docker Desktop
- Kubernetes включён в Docker Desktop
- kubectl
- Git

---

Проверка Kubernetes:

```bash
kubectl version --client
kubectl get nodes
```

## Подготовка secrets:

config/common-secret.yaml
```
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

config/incidents&monitors-secret.yaml
```
apiVersion: v1
kind: Secret
metadata:
  name: incidents-secret / monitors-secret
  namespace: uptime-monitor
type: Opaque
stringData: {}
```

config/notifications-secret.yaml
```
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

config/user-support-secret.yaml
```
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

postgres/secret.yaml
```
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

rabbitmq/secret.yaml
```
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

Создание namespace
```bash
kubectl apply -f k8s/namespace.yaml
```

Создание конфигурации
```bash
kubectl apply -f k8s/config/
```

PostgreSQL
```bash
kubectl apply -f k8s/postgres/
```

Redis
```bash
kubectl apply -f k8s/redis/
```

RabbitMQ
```bash
kubectl apply -f k8s/rabbitmq/
```

Probes
```bash
kubectl apply -f k8s/probes/
```

User Support
```bash
kubectl apply -f k8s/user-support/
```

Monitors
```bash
kubectl apply -f k8s/monitors/
```

Incidents
```bash
kubectl apply -f k8s/incidents/
```

Notifications
```bash
kubectl apply -f k8s/notifications/
```

Nginx
```bash
kubectl apply -f k8s/nginx/
```

---

## Проверка deployment

Все Pod:
```bash
kubectl get pods -n uptime-monitor
```

Services:
```bash
kubectl get svc -n uptime-monitor
```

Deployment:
```bash
kubectl get deployments -n uptime-monitor
```

Все ресурсы namespace:
```bash
kubectl get all -n uptime-monitor
```

Логи конкретного Pod:
```bash
kubectl logs -n uptime-monitor <pod-name>
```

Следить за логами в реальном времени:
```bash
kubectl logs -f -n uptime-monitor deploy/monitors-worker
```

---

## Database migrations

После первого запуска необходимо выполнить Django migrations.

user_support
```bash
kubectl apply -f k8s/user-support/migration-job.yaml
```

monitors
```bash
kubectl apply -f k8s/monitors/migration-job.yaml
```

incidents
```bash
kubectl apply -f k8s/incidents/migration-job.yaml
```

notifications
```bash
kubectl apply -f k8s/notifications/migration-job.yaml
```

---

# Docker Compose

Docker Compose используется для локального запуска проекта без Kubernetes.

```bash
docker compose up --build -d
```













