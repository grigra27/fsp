# Исправление проблем с правами доступа - Сводка 🔐

## 🚨 Проблема
```
PermissionError: [Errno 13] Permission denied: '/app/logs/app.log'
ValueError: Unable to configure handler 'app_file'
```

Gunicorn не мог запуститься из-за отсутствия прав на запись в директорию логов.

## ✅ Исправления

### 1. **Dockerfile.web** - исправлены права доступа
```dockerfile
# Создание директорий с правильными правами
RUN mkdir -p logs staticfiles && \
    chown -R django:django /app

# Сбор статических файлов
RUN DJANGO_SETTINGS_MODULE=fsp.production python manage.py collectstatic --noinput

# Обеспечение правильных прав после collectstatic
RUN chown -R django:django /app/logs /app/staticfiles

# Переключение на непривилегированного пользователя
USER django
```

### 2. **Dockerfile.bot** - улучшены права доступа
```dockerfile
# Создание директорий с правильными правами
RUN mkdir -p logs && \
    chown -R django:django /app && \
    chmod 755 /app/logs
```

### 3. **settings.py** - надежная конфигурация логирования
- ✅ Проверка доступности директории логов
- ✅ Тестирование прав на запись
- ✅ Fallback на консольное логирование при проблемах с файлами
- ✅ Автоматическое создание директории с правильными правами

```python
# Создание директории логов с проверкой прав
try:
    LOG_DIR.mkdir(exist_ok=True, mode=0o755)
    # Тест прав на запись
    test_file = LOG_DIR / 'test.log'
    test_file.touch()
    test_file.unlink()
    LOGGING_AVAILABLE = True
except (PermissionError, OSError):
    LOGGING_AVAILABLE = False
```

### 4. **GitHub Actions** - правильная настройка прав при деплое
```bash
# Создание директорий с правильными правами
mkdir -p fsp/logs fsp/staticfiles
chmod 755 fsp/logs fsp/staticfiles

# Создание базы данных если её нет
if [ ! -f "fsp/db.sqlite3" ]; then
  touch fsp/db.sqlite3
fi
chmod 664 fsp/db.sqlite3

# Установка правильного владельца (UID 1000 = django user в контейнере)
chown -R 1000:1000 fsp/ || true
```

## 🛠️ Новые инструменты

### **scripts/fix_permissions.sh** - автоматическое исправление прав
Скрипт выполняет:
- ✅ Остановку контейнеров
- ✅ Создание директорий с правильными правами
- ✅ Установку владельца файлов
- ✅ Обновление Docker образов
- ✅ Перезапуск с проверкой статуса

## 🔍 Диагностика проблем с правами

### Проверка прав на сервере:
```bash
# Проверка прав на директории
ls -la /opt/fair-sber-price/fsp/

# Проверка владельца файлов
ls -la /opt/fair-sber-price/fsp/logs/
ls -la /opt/fair-sber-price/fsp/db.sqlite3

# Проверка возможности записи
touch /opt/fair-sber-price/fsp/logs/test.log
rm /opt/fair-sber-price/fsp/logs/test.log
```

### Проверка в контейнере:
```bash
# Проверка пользователя в контейнере
docker exec fsp_web whoami
docker exec fsp_web id

# Проверка прав в контейнере
docker exec fsp_web ls -la /app/logs/
docker exec fsp_web touch /app/logs/test.log
```

## 🚀 Применение исправлений

### Автоматически (рекомендуется):
```bash
git add .
git commit -m "Fix permissions issues for logs and database"
git push origin main
```

GitHub Actions автоматически:
1. Пересоберет образы с исправленными правами
2. Настроит правильные права на сервере
3. Перезапустит контейнеры

### Вручную на сервере:
```bash
# Подключение к серверу
ssh root@your-server-ip

# Запуск скрипта исправления
cd /opt/fair-sber-price
./scripts/fix_permissions.sh
```

## 📊 Проверка результата

После применения исправлений:

### 1. Проверка статуса контейнеров:
```bash
docker-compose -f docker-compose.prod.yml ps
```

### 2. Проверка логов веб-приложения:
```bash
docker logs fsp_web --tail=20
```

### 3. Проверка health endpoint:
```bash
curl http://your-server-ip:8000/api/health/
```

### 4. Проверка файлов логов:
```bash
ls -la /opt/fair-sber-price/fsp/logs/
tail -f /opt/fair-sber-price/fsp/logs/app.log
```

## ✅ Ожидаемый результат

После исправлений:
- 🟢 Gunicorn запускается без ошибок прав доступа
- 🟢 Логи записываются в файлы (или в консоль при проблемах)
- 🟢 База данных доступна для записи
- 🟢 Статические файлы обслуживаются корректно
- 🟢 Все контейнеры работают стабильно

## 🔧 Если проблемы остаются

### 1. Запустите диагностику:
```bash
./scripts/fix_permissions.sh
```

### 2. Проверьте логи:
```bash
docker logs fsp_web --tail=50
docker logs fsp_telegram_bot --tail=50
```

### 3. Проверьте права вручную:
```bash
# На хосте
ls -la /opt/fair-sber-price/fsp/
chown -R 1000:1000 /opt/fair-sber-price/fsp/
chmod 755 /opt/fair-sber-price/fsp/logs
chmod 664 /opt/fair-sber-price/fsp/db.sqlite3
```

### 4. Перезапустите контейнеры:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## 📞 Поддержка

Если проблемы с правами доступа продолжаются:
1. Запустите `./scripts/fix_permissions.sh`
2. Соберите логи: `docker logs fsp_web > web_logs.txt`
3. Создайте Issue в GitHub с логами и описанием проблемы

---

**Права доступа теперь настроены правильно для стабильной работы в продакшене!** 🔐✨