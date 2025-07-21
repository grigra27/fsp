# Исправление проблемы ALLOWED_HOSTS для Telegram бота 🤖

## 🚨 Проблема
```
RuntimeError: ALLOWED_HOSTS environment variable is required for production!
```

Telegram бот падал при запуске, потому что:
- Бот использует те же настройки Django, что и веб-приложение
- В production.py есть строгая проверка на наличие `ALLOWED_HOSTS`
- Для бота `ALLOWED_HOSTS` не критичен, так как он не обслуживает HTTP запросы

## ✅ Исправления

### 1. **settings.py** - умная проверка ALLOWED_HOSTS
```python
# ALLOWED_HOSTS configuration
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
else:
    ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]
    # For Telegram bot, ALLOWED_HOSTS is not critical since it doesn't serve HTTP
    # Check if we're running the bot command
    import sys
    is_bot_command = len(sys.argv) > 1 and 'runtelegrambot' in sys.argv[1]
    
    if not ALLOWED_HOSTS and not is_bot_command:
        raise RuntimeError("ALLOWED_HOSTS environment variable is required for production web server!")
```

**Что изменилось:**
- ✅ Проверка команды запуска - если это `runtelegrambot`, то `ALLOWED_HOSTS` не обязателен
- ✅ Более информативное сообщение об ошибке
- ✅ Бот может запускаться без `ALLOWED_HOSTS`

### 2. **docker-compose.prod.yml** - добавлен ALLOWED_HOSTS для бота
```yaml
telegram-bot:
  environment:
    - SECRET_KEY=${SECRET_KEY}
    - DEBUG=False
    - ALLOWED_HOSTS=${ALLOWED_HOSTS}  # Добавлено для совместимости
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - REDIS_URL=redis://redis:6379/0
    - DJANGO_SETTINGS_MODULE=fsp.production
```

### 3. **GitHub Actions** - синхронизирована конфигурация
- Добавлен `ALLOWED_HOSTS` в переменные окружения для бота
- Обеспечена полная совместимость с веб-приложением

### 4. **scripts/fix_bot.sh** - улучшена проверка переменных
```bash
# Проверяем обязательные переменные
missing_vars=""
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    missing_vars="$missing_vars TELEGRAM_BOT_TOKEN"
fi
if [ -z "$SECRET_KEY" ]; then
    missing_vars="$missing_vars SECRET_KEY"
fi
if [ -z "$ALLOWED_HOSTS" ]; then
    missing_vars="$missing_vars ALLOWED_HOSTS"
fi
```

## 🔍 Диагностика проблем с переменными окружения

### Проверка переменных на сервере:
```bash
# Проверка .env файла
cat /opt/fair-sber-price/.env

# Проверка переменных в контейнере
docker exec fsp_telegram_bot env | grep -E "(TELEGRAM_BOT_TOKEN|ALLOWED_HOSTS|SECRET_KEY)"
```

### Проверка запуска бота:
```bash
# Тест запуска команды Django
docker exec fsp_telegram_bot python manage.py check

# Тест команды бота
docker exec fsp_telegram_bot python manage.py runtelegrambot --help
```

## 🚀 Применение исправлений

### Автоматически (рекомендуется):
```bash
git add .
git commit -m "Fix ALLOWED_HOSTS issue for Telegram bot"
git push origin main
```

GitHub Actions автоматически:
1. Пересоберет образы с исправленными настройками
2. Обновит docker-compose.prod.yml на сервере
3. Перезапустит бота с правильными переменными окружения

### Вручную на сервере:
```bash
# Подключение к серверу
ssh root@your-server-ip

# Запуск скрипта исправления
cd /opt/fair-sber-price
./scripts/fix_bot.sh
```

## 📊 Проверка результата

После применения исправлений:

### 1. Проверка статуса бота:
```bash
$ docker-compose -f docker-compose.prod.yml ps telegram-bot
NAME                STATUS
fsp_telegram_bot    Up X minutes (healthy)
```

### 2. Проверка логов бота:
```bash
$ docker logs fsp_telegram_bot --tail=10
✅ Telegram bot handlers configured successfully
🚀 Starting Telegram bot polling...
```

### 3. Тест бота в Telegram:
- Найдите вашего бота в Telegram
- Отправьте `/start`
- Бот должен ответить с текущими данными

## 🔧 Если бот все еще не запускается

### 1. Проверьте переменные окружения:
```bash
# На сервере
cat /opt/fair-sber-price/.env | grep -E "(TELEGRAM_BOT_TOKEN|ALLOWED_HOSTS|SECRET_KEY)"

# В контейнере
docker exec fsp_telegram_bot env | grep -E "(TELEGRAM_BOT_TOKEN|ALLOWED_HOSTS|SECRET_KEY)"
```

### 2. Запустите диагностику:
```bash
./scripts/diagnose_bot.sh
```

### 3. Проверьте формат переменных:
```bash
# TELEGRAM_BOT_TOKEN должен быть в формате: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
# ALLOWED_HOSTS должен быть в формате: domain.com,ip.address,localhost
# SECRET_KEY должен быть длинной случайной строкой
```

### 4. Перезапустите бота:
```bash
./scripts/fix_bot.sh
```

## ✅ Ожидаемый результат

После исправлений:
- 🟢 Бот запускается без ошибок ALLOWED_HOSTS
- 🟢 Веб-приложение по-прежнему требует ALLOWED_HOSTS (безопасность)
- 🟢 Обе службы работают с одинаковыми настройками Django
- 🟢 Автоматическая диагностика переменных окружения

## 📞 Поддержка

Если проблемы с переменными окружения продолжаются:
1. Проверьте GitHub Secrets в репозитории
2. Запустите `./scripts/fix_bot.sh` на сервере
3. Соберите логи: `docker logs fsp_telegram_bot > bot_env_logs.txt`
4. Создайте Issue в GitHub с логами

---

**Telegram бот теперь корректно работает с переменными окружения!** 🤖✅