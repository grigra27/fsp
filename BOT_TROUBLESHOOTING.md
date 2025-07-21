# Устранение проблем с Telegram ботом 🤖

## 🔍 Быстрая диагностика

### Шаг 1: Проверьте статус контейнеров
```bash
cd /opt/fair-sber-price
docker-compose -f docker-compose.prod.yml ps
```

### Шаг 2: Посмотрите логи бота
```bash
docker logs fsp_telegram_bot --tail=50
```

### Шаг 3: Запустите диагностический скрипт
```bash
./scripts/diagnose_bot.sh
```

## 🛠️ Автоматическое исправление

### Запустите скрипт исправления:
```bash
cd /opt/fair-sber-price
./scripts/fix_bot.sh
```

Этот скрипт:
- ✅ Остановит и пересоздаст контейнер бота
- ✅ Обновит образ до последней версии
- ✅ Проверит переменные окружения
- ✅ Создаст необходимые файлы и директории
- ✅ Покажет логи для диагностики

## 🔧 Ручное исправление

### 1. Проверка токена бота
```bash
# Проверьте .env файл
cat /opt/fair-sber-price/.env | grep TELEGRAM_BOT_TOKEN

# Токен должен быть в формате: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. Пересоздание контейнера бота
```bash
cd /opt/fair-sber-price

# Остановка и удаление
docker-compose -f docker-compose.prod.yml stop telegram-bot
docker-compose -f docker-compose.prod.yml rm -f telegram-bot

# Обновление образа
docker pull ghcr.io/grigra27/fair_sber_price-bot:latest

# Запуск
docker-compose -f docker-compose.prod.yml up -d telegram-bot
```

### 3. Проверка базы данных
```bash
# Убедитесь, что база данных существует
ls -la /opt/fair-sber-price/fsp/db.sqlite3

# Если файла нет, создайте его
touch /opt/fair-sber-price/fsp/db.sqlite3
chmod 664 /opt/fair-sber-price/fsp/db.sqlite3
```

### 4. Проверка логов
```bash
# Создайте директорию для логов если её нет
mkdir -p /opt/fair-sber-price/fsp/logs
chmod 755 /opt/fair-sber-price/fsp/logs

# Проверьте логи приложения
tail -f /opt/fair-sber-price/fsp/logs/app.log
```

## 🚨 Частые проблемы и решения

### ❌ Проблема: "TELEGRAM_BOT_TOKEN not set"
**Решение:**
```bash
# Проверьте GitHub Secrets в репозитории
# Убедитесь, что TELEGRAM_BOT_TOKEN добавлен правильно
# Перезапустите деплой через GitHub Actions
```

### ❌ Проблема: "Database is locked"
**Решение:**
```bash
# Остановите все контейнеры
docker-compose -f docker-compose.prod.yml down

# Проверьте права на базу данных
chmod 664 /opt/fair-sber-price/fsp/db.sqlite3

# Запустите снова
docker-compose -f docker-compose.prod.yml up -d
```

### ❌ Проблема: "Connection refused to Redis"
**Решение:**
```bash
# Проверьте статус Redis
docker-compose -f docker-compose.prod.yml ps redis

# Перезапустите Redis
docker-compose -f docker-compose.prod.yml restart redis

# Подождите и запустите бота
sleep 10
docker-compose -f docker-compose.prod.yml restart telegram-bot
```

### ❌ Проблема: "Import error" или "Module not found"
**Решение:**
```bash
# Пересоберите и обновите образы через GitHub Actions
git add .
git commit -m "Fix bot dependencies"
git push origin main

# Или обновите образ вручную
docker pull ghcr.io/grigra27/fair_sber_price-bot:latest
docker-compose -f docker-compose.prod.yml up -d telegram-bot
```

## 📊 Мониторинг бота

### Проверка здоровья бота
```bash
# Статус контейнера
docker inspect fsp_telegram_bot --format='{{.State.Status}}'

# Health check
docker inspect fsp_telegram_bot --format='{{.State.Health.Status}}'

# Время работы
docker inspect fsp_telegram_bot --format='{{.State.StartedAt}}'
```

### Тестирование бота
1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Проверьте ответ бота
4. Попробуйте команды `/info` и `/help`

## 🔄 Автоматическое восстановление

Бот настроен на автоматический перезапуск:
- **Docker restart policy**: `unless-stopped`
- **Health checks**: каждые 60 секунд
- **Systemd service**: автозапуск при перезагрузке сервера

### Проверка автозапуска
```bash
# Статус systemd сервиса
systemctl status fair-sber-price.service

# Включение автозапуска (если отключен)
systemctl enable fair-sber-price.service
```

## 📞 Получение помощи

Если проблема не решается:

1. **Соберите диагностическую информацию:**
   ```bash
   ./scripts/diagnose_bot.sh > bot_diagnosis.txt
   ```

2. **Создайте Issue в GitHub** с:
   - Описанием проблемы
   - Логами бота
   - Результатами диагностики

3. **Временное решение** - перезапуск всего стека:
   ```bash
   cd /opt/fair-sber-price
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

---

**Помните**: После любых изменений в коде бота нужно пересобрать образ через GitHub Actions (git push) или обновить образ вручную!