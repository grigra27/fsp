# Исправление Health Check - Сводка 🏥

## 🚨 Проблема
Контейнер `fsp_web` показывал статус `unhealthy` из-за неработающего health check:
- Health check использовал `requests` библиотеку, которая не была установлена в контейнере
- Неправильное время ожидания запуска (start_period)

## ✅ Исправления

### 1. **Dockerfile.web** - добавлен curl и исправлен health check
```dockerfile
# Установка curl для health check
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r django && useradd -r -g django django

# Health check с использованием curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1
```

### 2. **docker-compose.prod.yml** - обновлен health check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 3. **GitHub Actions** - синхронизирована конфигурация
- Обновлен встроенный docker-compose.prod.yml в workflow
- Используется curl вместо python requests
- Правильное время ожидания запуска

### 4. **Health Check Endpoint** - уже существует
- ✅ `/api/health/` endpoint работает корректно
- ✅ Проверяет базу данных, кеш, внешние API
- ✅ Возвращает детальную информацию о состоянии системы

## 🛠️ Новые инструменты

### **scripts/test_health.sh** - тестирование health check
Скрипт проверяет:
- ✅ Health check изнутри контейнера
- ✅ Health check с хоста
- ✅ Health check с внешнего IP
- ✅ Детальную информацию о состоянии
- ✅ Историю health checks

## 🔍 Диагностика health check

### Быстрая проверка:
```bash
# Статус контейнера
docker-compose -f docker-compose.prod.yml ps

# Health status
docker inspect fsp_web --format='{{.State.Health.Status}}'

# Тест health endpoint
curl -f http://localhost:8000/api/health/
```

### Полная диагностика:
```bash
# Запуск диагностического скрипта
./scripts/test_health.sh

# Детальная информация
curl -s http://localhost:8000/api/health/ | python3 -m json.tool
```

### История health checks:
```bash
# Последние health check логи
docker inspect fsp_web --format='{{range .State.Health.Log}}{{.Start}} - {{.Output}}{{end}}' | tail -5
```

## 🚀 Применение исправлений

### Автоматически (рекомендуется):
```bash
git add .
git commit -m "Fix health check using curl instead of requests"
git push origin main
```

GitHub Actions автоматически:
1. Пересоберет образ с установленным curl
2. Обновит docker-compose.prod.yml на сервере
3. Перезапустит контейнеры с новым health check

### Вручную на сервере:
```bash
# Подключение к серверу
ssh root@your-server-ip

# Тестирование health check
cd /opt/fair-sber-price
./scripts/test_health.sh

# Если нужно - обновление образов
docker pull ghcr.io/grigra27/fair_sber_price-web:latest
docker-compose -f docker-compose.prod.yml up -d web
```

## 📊 Ожидаемый результат

После применения исправлений:

### 1. Статус контейнера:
```bash
$ docker-compose -f docker-compose.prod.yml ps
NAME           STATUS
fsp_web        Up X minutes (healthy)  # Вместо (unhealthy)
fsp_redis      Up X minutes (healthy)
fsp_telegram_bot  Up X minutes (healthy)
```

### 2. Health check работает:
```bash
$ curl http://localhost:8000/api/health/
{
  "status": "healthy",
  "timestamp": "2025-07-21T22:50:00.000Z",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "api_success_rate": "100.0%",
    "moex_api": "ok"
  },
  "version": "1.0.0"
}
```

### 3. Docker health status:
```bash
$ docker inspect fsp_web --format='{{.State.Health.Status}}'
healthy
```

## 🔧 Если health check все еще не работает

### 1. Проверьте логи контейнера:
```bash
docker logs fsp_web --tail=20
```

### 2. Тестируйте health endpoint вручную:
```bash
# Изнутри контейнера
docker exec fsp_web curl -f http://localhost:8000/api/health/

# С хоста
curl -f http://localhost:8000/api/health/
```

### 3. Проверьте Django приложение:
```bash
# Проверка Django
docker exec fsp_web python manage.py check

# Тест базы данных
docker exec fsp_web python manage.py shell -c "from django.db import connection; connection.cursor().execute('SELECT 1')"
```

### 4. Перезапустите контейнер:
```bash
docker-compose -f docker-compose.prod.yml restart web
```

## 📈 Мониторинг health check

### Автоматический мониторинг:
- Docker проверяет health каждые 30 секунд
- При 3 неудачных проверках контейнер помечается как unhealthy
- Systemd автоматически перезапускает сервис при проблемах

### Ручной мониторинг:
```bash
# Непрерывный мониторинг
watch -n 5 'docker inspect fsp_web --format="{{.State.Health.Status}}"'

# Логи health checks
docker inspect fsp_web --format='{{json .State.Health}}' | python3 -m json.tool
```

## 📞 Поддержка

Если health check не работает после всех исправлений:
1. Запустите `./scripts/test_health.sh`
2. Соберите логи: `docker logs fsp_web > web_health_logs.txt`
3. Создайте Issue в GitHub с результатами диагностики

---

**Health check теперь работает надежно с использованием curl!** 🏥✅