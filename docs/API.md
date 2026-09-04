# API Documentation

## Общая информация

API состоит из четырёх Django REST Framework сервисов:

| Сервис | Назначение | Base path |
|---|---|---|
| `user_support` | Регистрация, авторизация и управление пользователями | `/api/v1/` |
| `monitors` | Управление мониторами и ручные проверки | `/api/v1/monitoring/` |
| `incidents` | Управление инцидентами | `/api/v1/incidents/` |
| `notifications` | Управление уведомлениями | `/api/v1/notifications/` |

### Аутентификация

Защищённые endpoints используют JWT-аутентификацию:

```http
Authorization: Bearer <access_token>
```

Публичные endpoints отмечены как `AllowAny`.

---

# 1. User Support API

Сервис отвечает за регистрацию пользователей, JWT-аутентификацию, GitHub OAuth и управление профилем.

## 1.1. Регистрация пользователя

```http
POST /api/v1/register/
```

**Доступ:** публичный.

Создаёт нового пользователя.

Request body определяется `UserSerializer`.

Пример:

```json
{
  "username": "user",
  "email": "user@example.com",
  "password": "password"
}
```

> Точный набор и обязательность полей определяются `UserSerializer`.

## 1.2. GitHub OAuth

```http
POST /api/v1/auth/github/
```

**Доступ:** публичный.

Авторизует пользователя через временный OAuth `code`, полученный от GitHub.

Request body:

```json
{
  "code": "github_oauth_code"
}
```

Используется `LoginCodeSerializer`.

Успешный ответ:

```http
200 OK
```

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>",
  "user": {
    "id": 1,
    "username": "github_user",
    "email": "user@example.com"
  }
}
```

Если пользователя с таким GitHub username нет, он создаётся автоматически.

Возможные ошибки:

```http
400 Bad Request
```

```json
{
  "error": "Невалидный код или ошибка на стороне GitHub."
}
```

или:

```json
{
  "detail": "Аккаунт деактивирован."
}
```

## 1.3. Профиль пользователя

```http
GET /api/v1/profile/
PATCH /api/v1/profile/
```

**Доступ:** авторизованный пользователь.

Endpoint работает с профилем текущего пользователя.

### GET

Возвращает профиль текущего пользователя.

Формат определяется `PersonalUserSerializer`.

### PATCH

Частично обновляет профиль текущего пользователя.

Формат запроса определяется `PersonalUserSerializer`.

## 1.4. Деактивация аккаунта

```http
POST /api/v1/profile/deactivate/
```

**Доступ:** авторизованный пользователь.

Деактивирует аккаунт текущего пользователя.

Успешный ответ:

```http
200 OK
```

```json
{
  "detail": "Аккаунт успешно деактивирован."
}
```

## 1.5. Список пользователей

```http
GET /api/v1/users/all/
```

**Доступ:** только администратор (`IsAdminUser`).

Возвращает список пользователей.

Используется `UserListSerializer`. Пользователи выбираются вместе с `settings` и сортируются по `is_active`.

## 1.6. Получение JWT токенов

```http
POST /api/v1/auth/token/
```

**Доступ:** публичный.

Использует `TokenObtainPairView`.

Пример ответа:

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

## 1.7. Обновление JWT access token

```http
POST /api/v1/auth/token/refresh/
```

**Доступ:** публичный.

Request body:

```json
{
  "refresh": "<refresh_token>"
}
```

## 1.8. Проверка JWT token

```http
POST /api/v1/auth/token/verify/
```

**Доступ:** публичный.

Request body:

```json
{
  "token": "<jwt_token>"
}
```

---

# 2. Monitors API

Сервис отвечает за создание и управление мониторами, историю проверок и ручной запуск проверки.

Основной ресурс:

```http
/api/v1/monitoring/
```

Используется `MonitorViewSet` с `ModelViewSet`.

**Доступ:** авторизованный пользователь.

Пользователь работает только со своими мониторами.

## 2.1. Список мониторов

```http
GET /api/v1/monitoring/
```

Возвращает мониторы текущего пользователя.

Сортировка — по `id` в обратном порядке.

Формат определяется `MonitorSerializer`.

## 2.2. Создание монитора

```http
POST /api/v1/monitoring/
```

Создаёт монитор для текущего пользователя.

`user_id` устанавливается сервером.

Request body определяется `MonitorSerializer`.

Пример:

```json
{
  "name": "My website",
  "url": "https://example.com"
}
```

> Названия и обязательность полей приведены только как пример. Точный формат определяется `MonitorSerializer`.

## 2.3. Получение монитора

```http
GET /api/v1/monitoring/{id}/
```

Возвращает конкретный монитор текущего пользователя.

## 2.4. Полное обновление монитора

```http
PUT /api/v1/monitoring/{id}/
```

Полностью обновляет монитор.

## 2.5. Частичное обновление монитора

```http
PATCH /api/v1/monitoring/{id}/
```

Частично обновляет монитор.

## 2.6. Удаление монитора

```http
DELETE /api/v1/monitoring/{id}/
```

Удаляет монитор текущего пользователя.

## 2.7. История проверок

```http
GET /api/v1/monitoring/{id}/history/
```

Возвращает историю проверок конкретного монитора.

Endpoint возвращает до 100 результатов проверки.

Формат элементов определяется `CheckResultSerializer`.

## 2.8. Ручная проверка

```http
POST /api/v1/monitoring/{monitor_id}/manual/
```

**Доступ:** авторизованный пользователь.

Запускает принудительную проверку монитора.

Проверка выполняется асинхронно через Celery task `run_single_monitor_task`.

Успешный ответ:

```http
202 Accepted
```

```json
{
  "detail": "Success check manually My website"
}
```

Endpoint использует:

- `BurstManualCheckThrottle`
- `DailyManualCheckThrottle`

Конкретные лимиты определяются настройками throttle-классов.

---

# 3. Incidents API

Сервис отвечает за управление инцидентами мониторинга.

Основной ресурс:

```http
/api/v1/incidents/
```

Используется `IncidentsViewSet` с `ModelViewSet`.

**Доступ:** авторизованный пользователь.

Пользователь получает только свои инциденты.

## 3.1. Список инцидентов

```http
GET /api/v1/incidents/
```

Возвращает инциденты текущего пользователя.

Сортировка:

1. `started_at` — по убыванию;
2. `status` — по возрастанию.

Формат определяется `IncidentSerializer`.

## 3.2. Создание инцидента

```http
POST /api/v1/incidents/
```

Создаёт инцидент.

Формат запроса и ответа определяется `IncidentSerializer`.

## 3.3. Получение инцидента

```http
GET /api/v1/incidents/{id}/
```

Возвращает конкретный инцидент текущего пользователя.

## 3.4. Полное обновление инцидента

```http
PUT /api/v1/incidents/{id}/
```

Полностью обновляет инцидент.

## 3.5. Частичное обновление инцидента

```http
PATCH /api/v1/incidents/{id}/
```

Частично обновляет инцидент.

## 3.6. Удаление инцидента

```http
DELETE /api/v1/incidents/{id}/
```

Удаляет инцидент текущего пользователя.

---

# 4. Notifications API

Сервис отвечает за управление уведомлениями пользователя.

Основной ресурс:

```http
/api/v1/notifications/
```

Используется `NotificationsViewSet` с `ModelViewSet`.

**Доступ:** авторизованный пользователь.

Пользователь получает только собственные уведомления.

Поддерживается фильтрация через `DjangoFilterBackend` и `NotificationFilter`.

## 4.1. Список уведомлений

```http
GET /api/v1/notifications/
```

Возвращает уведомления текущего пользователя.

Поддерживает фильтрацию, определённую `NotificationFilter`.

Формат элементов определяется `NotificationSerializer`.

## 4.2. Создание уведомления

```http
POST /api/v1/notifications/
```

Создаёт уведомление.

`user_id` устанавливается сервером на основании текущего пользователя.

Формат запроса и ответа определяется `NotificationSerializer`.

## 4.3. Получение уведомления

```http
GET /api/v1/notifications/{id}/
```

Возвращает конкретное уведомление текущего пользователя.

## 4.4. Полное обновление уведомления

```http
PUT /api/v1/notifications/{id}/
```

Полностью обновляет уведомление.

## 4.5. Частичное обновление уведомления

```http
PATCH /api/v1/notifications/{id}/
```

Частично обновляет уведомление.

## 4.6. Удаление уведомления

```http
DELETE /api/v1/notifications/{id}/
```

Удаляет уведомление текущего пользователя.

---

# 5. HTTP Status Codes

| Код | Значение |
|---|---|
| `200 OK` | Успешный запрос |
| `201 Created` | Ресурс успешно создан |
| `202 Accepted` | Запрос принят на асинхронное выполнение |
| `204 No Content` | Ресурс успешно удалён / ответ без тела |
| `400 Bad Request` | Некорректные данные запроса |
| `401 Unauthorized` | Требуется аутентификация |
| `403 Forbidden` | Недостаточно прав |
| `404 Not Found` | Ресурс не найден |
| `429 Too Many Requests` | Превышен лимит запросов |

---

# 6. OpenAPI / Swagger

Каждый Django-сервис генерирует собственную OpenAPI-схему с помощью `drf-spectacular`.

Для каждого сервиса предусмотрены:

```text
/api/v1/<service>/schema/
/api/v1/<service>/docs/
/api/v1/<service>/redoc/
```

Актуальные URL конкретного сервиса определяются его Django URL configuration.

В дальнейшем Swagger UI может быть объединён в единую точку входа для всех четырёх API без объединения самих Django-приложений.
