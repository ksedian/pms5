# Admin Interface API Documentation

**Модель:** Claude Sonnet 4

Полноценный административный интерфейс для управления пользователями, ролями и разрешениями в системе аутентификации MES.

## Обзор

Admin Interface предоставляет защищенные API endpoints для:
- Управления пользователями (активация/деактивация, разблокировка)
- CRUD операций с ролями
- CRUD операций с разрешениями
- Назначения/отзыва ролей пользователям
- Назначения/отзыва разрешений ролям
- Просмотра audit logs

## Безопасность

**Все endpoints защищены RBAC:**
- `@require_role('admin')` - только администраторы
- `@require_permission('resource:action')` - гранулярные разрешения
- **Audit logging** всех административных действий
- **Валидация входных данных** и защита от инъекций

## API Endpoints

### 👥 User Management

#### GET /api/admin/users
**Описание:** Список всех пользователей  
**Права:** admin role  
**Ответ:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "is_active": true,
      "is_locked": false,
      "roles": ["admin"],
      "permissions": ["*:*"]
    }
  ],
  "total": 1
}
```

#### GET /api/admin/users/{user_id}
**Описание:** Детали конкретного пользователя  
**Права:** admin role  
**Ответ:**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_2fa_enabled": false,
    "is_active": true,
    "is_locked": false,
    "last_login": "2025-07-01T16:00:00Z",
    "roles": ["admin"],
    "permissions": ["*:*"]
  }
}
```

#### POST /api/admin/users/{user_id}/activate
**Описание:** Активировать пользователя  
**Права:** admin role  
**Ответ:**
```json
{
  "message": "User activated successfully"
}
```

#### POST /api/admin/users/{user_id}/deactivate
**Описание:** Деактивировать пользователя  
**Права:** admin role  
**Ограничения:** Нельзя деактивировать самого себя  
**Ответ:**
```json
{
  "message": "User deactivated successfully"
}
```

#### POST /api/admin/users/{user_id}/unlock
**Описание:** Разблокировать пользователя  
**Права:** admin role  
**Ответ:**
```json
{
  "message": "User unlocked successfully"
}
```

### 🎭 Role Management

#### GET /api/admin/roles
**Описание:** Список всех ролей  
**Права:** `roles:read`  
**Ответ:**
```json
{
  "roles": [
    {
      "id": 1,
      "name": "admin",
      "description": "System administrator",
      "is_system_role": true,
      "permissions": ["*:*"]
    }
  ],
  "total": 4
}
```

#### POST /api/admin/roles
**Описание:** Создать новую роль  
**Права:** `roles:create`  
**Запрос:**
```json
{
  "name": "supervisor",
  "description": "Production supervisor role"
}
```
**Ответ:**
```json
{
  "message": "Role created successfully",
  "role": {
    "id": 5,
    "name": "supervisor",
    "description": "Production supervisor role",
    "is_system_role": false,
    "permissions": []
  }
}
```

#### PUT /api/admin/roles/{role_id}
**Описание:** Обновить роль  
**Права:** `roles:update`  
**Ограничения:** Нельзя изменять системные роли  
**Запрос:**
```json
{
  "name": "lead_supervisor",
  "description": "Lead production supervisor"
}
```

#### DELETE /api/admin/roles/{role_id}
**Описание:** Удалить роль  
**Права:** `roles:delete`  
**Ограничения:** 
- Нельзя удалять системные роли
- Нельзя удалять роли, назначенные пользователям

### 🔑 Permission Management

#### GET /api/admin/permissions
**Описание:** Список всех разрешений  
**Права:** `permissions:read`  
**Ответ:**
```json
{
  "permissions": [
    {
      "id": 1,
      "name": "tasks:read",
      "description": "Read task information",
      "resource": "tasks",
      "action": "read"
    }
  ],
  "total": 20
}
```

#### POST /api/admin/permissions
**Описание:** Создать новое разрешение  
**Права:** `permissions:create`  
**Запрос:**
```json
{
  "name": "inventory:manage",
  "description": "Manage inventory items",
  "resource": "inventory",
  "action": "manage"
}
```

#### PUT /api/admin/permissions/{permission_id}
**Описание:** Обновить разрешение  
**Права:** `permissions:update`  
**Запрос:**
```json
{
  "name": "inventory:full_access",
  "description": "Full access to inventory management"
}
```

#### DELETE /api/admin/permissions/{permission_id}
**Описание:** Удалить разрешение  
**Права:** `permissions:delete`  
**Ограничения:** Нельзя удалять разрешения, назначенные ролям

### 🔗 Role-User Assignments

#### POST /api/admin/users/{user_id}/roles
**Описание:** Назначить роль пользователю  
**Права:** `users:update`  
**Запрос:**
```json
{
  "role_id": 2
}
```
**Ответ:**
```json
{
  "message": "Role assigned successfully"
}
```

#### DELETE /api/admin/users/{user_id}/roles/{role_id}
**Описание:** Отозвать роль у пользователя  
**Права:** `users:update`  
**Ограничения:** Нельзя отозвать admin роль у самого себя  
**Ответ:**
```json
{
  "message": "Role revoked successfully"
}
```

### 🔗 Role-Permission Assignments

#### POST /api/admin/roles/{role_id}/permissions
**Описание:** Назначить разрешение роли  
**Права:** `roles:update`  
**Запрос:**
```json
{
  "permission_id": 5
}
```

#### DELETE /api/admin/roles/{role_id}/permissions/{permission_id}
**Описание:** Отозвать разрешение у роли  
**Права:** `roles:update`

### 📋 Audit Logs

#### GET /api/admin/audit-logs
**Описание:** Просмотр audit logs с фильтрацией  
**Права:** `audit_logs:read`  
**Параметры запроса:**
- `page` (int): Номер страницы (default: 1)
- `per_page` (int): Записей на страницу (max: 100, default: 50)
- `event_type` (string): Тип события для фильтрации
- `user_id` (int): ID пользователя для фильтрации
- `success` (bool): Фильтр по успешности события

**Пример запроса:**
```
GET /api/admin/audit-logs?page=1&per_page=25&event_type=role_assignment&success=true
```

**Ответ:**
```json
{
  "audit_logs": [
    {
      "id": 123,
      "user_id": 1,
      "username": "admin",
      "event_type": "role_assignment",
      "event_description": "Admin admin assigned role engineer to user john",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "success": true,
      "metadata": {
        "action": "assign_role",
        "target_user_id": 5,
        "role_id": 2
      },
      "timestamp": "2025-07-01T16:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 156,
    "pages": 7,
    "has_next": true,
    "has_prev": false
  }
}
```

## Использование с curl

### Аутентификация
Все requests требуют JWT token в заголовке:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:5000/api/admin/users
```

### Примеры запросов

**Список пользователей:**
```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/admin/users
```

**Создание роли:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "supervisor", "description": "Production supervisor"}' \
  http://localhost:5000/api/admin/roles
```

**Назначение роли пользователю:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role_id": 2}' \
  http://localhost:5000/api/admin/users/5/roles
```

**Просмотр audit logs:**
```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/api/admin/audit-logs?page=1&per_page=10&event_type=role_assignment"
```

## Коды ошибок

| Код | Описание | Причина |
|-----|----------|---------|
| 400 | Bad Request | Неверные данные запроса |
| 401 | Unauthorized | Отсутствует или неверный JWT token |
| 403 | Forbidden | Недостаточно прав доступа |
| 404 | Not Found | Ресурс не найден |
| 409 | Conflict | Конфликт данных (дублирование) |
| 500 | Internal Error | Ошибка сервера |

## Audit Events

Все административные действия логируются со следующими типами событий:

| Event Type | Описание |
|------------|----------|
| `admin_access` | Доступ к административным функциям |
| `user_activation` | Активация пользователя |
| `user_deactivation` | Деактивация пользователя |
| `account_unlock` | Разблокировка аккаунта |
| `role_creation` | Создание роли |
| `role_update` | Обновление роли |
| `role_deletion` | Удаление роли |
| `permission_creation` | Создание разрешения |
| `permission_update` | Обновление разрешения |
| `permission_deletion` | Удаление разрешения |
| `role_assignment` | Назначение роли пользователю |
| `role_revocation` | Отзыв роли у пользователя |
| `permission_assignment` | Назначение разрешения роли |
| `permission_revocation` | Отзыв разрешения у роли |
| `audit_access` | Доступ к audit logs |

## Безопасность и ограничения

### Защитные механизмы:
1. **RBAC enforcement** - проверка ролей и разрешений на каждом endpoint
2. **Self-protection** - нельзя деактивировать себя или отозвать свою admin роль
3. **System role protection** - системные роли нельзя изменять/удалять
4. **Dependency checks** - нельзя удалять роли/разрешения, которые используются
5. **Input validation** - валидация и санитизация всех входных данных
6. **Audit logging** - логирование всех административных действий

### Рекомендации:
- Используйте HTTPS в продакшене
- Регулярно ротируйте JWT tokens
- Мониторьте audit logs на подозрительную активность
- Ограничьте количество администраторов
- Используйте принцип минимальных привилегий

## Заключение

Обновленный Admin Interface полностью соответствует требованиям Current Feature Step 6:
- ✅ **RBAC защита** всех endpoints
- ✅ **Полный CRUD** для ролей и разрешений
- ✅ **Управление назначениями** ролей и разрешений
- ✅ **Comprehensive audit logging** всех действий
- ✅ **Безопасность и валидация** на всех уровнях

Система готова для административного управления пользователями и ролями в производственной среде. 