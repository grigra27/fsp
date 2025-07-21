# 🚀 Руководство по деплою на DigitalOcean

## 📋 Архитектура

Проект разделен на независимые сервисы:
- **Web Service** - Django веб-приложение (порт 8000)
- **Telegram Bot Service** - Telegram бот (независимый процесс)
- **Redis** - Кеширование и сессии
- **Nginx** - Reverse proxy и статические файлы

## 🛠️ Подготовка к деплою

### 1. Настройка GitHub Secrets

В настройках вашего GitHub репозитория добавьте следующие секреты:

```
DO_HOST=your-server-ip
DO_USERNAME=root
DO_SSH_KEY=your-private-ssh-key
DO_PORT=22
SECRET_KEY=your-very-secure-secret-key-50-chars-minimum
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

### 2. Создание DigitalOcean Droplet

1. Создайте Ubuntu 22.04 droplet (минимум 1GB RAM)
2. Настройте SSH ключи
3. Убедитесь, что Docker установлен (обычно уже есть на DigitalOcean droplets)
4. Обновите DNS записи для вашего домена

### 3. Первоначальная настройка сервера

```bash
# Скопируйте скрипт на сервер
scp scripts/setup-server.sh root@your-server-ip:/tmp/

# Запустите настройку
ssh root@your-server-ip
chmod +x /tmp/setup-server.sh
/tmp/setup-server.sh
```

### 4. Настройка переменных окружения

```bash
cd /opt/fair-sber-price
cp .env.template .env
nano .env
```

Заполните все необходимые переменные:
```env
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
REDIS_URL=redis://redis:6379/0
```

## 🔄 Автоматический деплой

### GitHub Actions Workflow

Автоматический деплой настроен через GitHub Actions:

1. **Push в main/master** → автоматический деплой
2. **Pull Request** → только тестирование
3. **Сборка Docker образов** → GitHub Container Registry
4. **Деплой на сервер** → обновление контейнеров

### Процесс деплоя:

1. Тестирование кода
2. Сборка Docker образов для web и bot
3. Публикация в GitHub Container Registry
4. SSH подключение к серверу
5. Обновление кода и контейнеров
6. Проверка работоспособности

## 🐳 Docker Compose Services

### Web Service (Dockerfile.web)
- Django приложение с Gunicorn
- Статические файлы через WhiteNoise
- Health checks
- Автоматический restart

### Bot Service (Dockerfile.bot)
- Независимый Telegram бот
- Использует ту же базу данных
- Автоматический restart
- Логирование в общие файлы

### Redis Service
- Кеширование данных
- Сессии пользователей
- Персистентное хранилище

### Nginx Service
- Reverse proxy для web
- Статические файлы
- Rate limiting
- SSL termination (готово к настройке)

## 🔧 Управление сервисами

### Основные команды:

```bash
# Статус сервисов
systemctl status fair-sber-price
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f telegram-bot

# Перезапуск
systemctl restart fair-sber-price

# Обновление (ручное)
cd /opt/fair-sber-price
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build

# Резервное копирование
./backup.sh
```

### Мониторинг:

```bash
# Проверка здоровья
curl http://localhost/api/health/

# Использование ресурсов
docker stats

# Логи nginx
docker-compose -f docker-compose.prod.yml logs nginx
```

## 🔒 SSL/HTTPS настройка

### Получение SSL сертификата (Let's Encrypt):

```bash
# Установка certbot
apt install certbot

# Получение сертификата
certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Копирование сертификатов
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/fair-sber-price/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/fair-sber-price/ssl/key.pem

# Обновление nginx.conf (раскомментировать HTTPS блок)
nano nginx.conf

# Перезапуск nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Автообновление сертификатов:

```bash
# Добавить в crontab
0 12 * * * /usr/bin/certbot renew --quiet && /usr/local/bin/docker-compose -f /opt/fair-sber-price/docker-compose.prod.yml restart nginx
```

## 📊 Мониторинг и логи

### Структура логов:
```
/opt/fair-sber-price/fsp/logs/
├── app.log          # Основные логи приложения
├── error.log        # Только ошибки
└── app.log.1        # Ротированные логи
```

### Мониторинг производительности:
- Health check: `http://your-domain.com/api/health/`
- Заголовки времени ответа: `X-Response-Time`
- Docker stats для использования ресурсов

## 🚨 Устранение неполадок

### Проблемы с контейнерами:
```bash
# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Перезапуск проблемного сервиса
docker-compose -f docker-compose.prod.yml restart web
docker-compose -f docker-compose.prod.yml restart telegram-bot

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs --tail=100 web
```

### Проблемы с базой данных:
```bash
# Вход в контейнер web
docker-compose -f docker-compose.prod.yml exec web bash

# Миграции
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser
```

### Проблемы с Telegram ботом:
```bash
# Проверка логов бота
docker-compose -f docker-compose.prod.yml logs telegram-bot

# Перезапуск только бота
docker-compose -f docker-compose.prod.yml restart telegram-bot

# Тест подключения к Telegram API
docker-compose -f docker-compose.prod.yml exec telegram-bot python -c "
import requests
response = requests.get('https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe')
print(response.json())
"
```

## 📈 Масштабирование

### Увеличение производительности:
```bash
# Больше workers для web
# В docker-compose.prod.yml изменить команду:
command: ["gunicorn", "fsp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "5"]

# Масштабирование через docker-compose
docker-compose -f docker-compose.prod.yml up -d --scale web=2
```

### Мониторинг ресурсов:
```bash
# Использование памяти и CPU
docker stats --no-stream

# Размер логов
du -sh /opt/fair-sber-price/fsp/logs/

# Размер базы данных
ls -lh /opt/fair-sber-price/fsp/db.sqlite3
```

## 🔄 Обновления

### Автоматические обновления через GitHub:
1. Push в main ветку
2. GitHub Actions автоматически деплоит
3. Проверка через health check

### Ручные обновления:
```bash
cd /opt/fair-sber-price
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

## 📞 Поддержка

При проблемах проверьте:
1. Логи сервисов: `docker-compose logs`
2. Health check: `curl http://localhost/api/health/`
3. Статус системы: `systemctl status fair-sber-price`
4. Ресурсы сервера: `htop`, `df -h`