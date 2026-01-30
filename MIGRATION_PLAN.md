# План миграции проекта с Digital Ocean на Timeweb

## 📋 Общая информация
- **Текущий хостинг**: Digital Ocean
- **Новый хостинг**: Timeweb
- **Текущий домен**: fsp.onbr.site
- **Новый домен**: fsp.insflow.online

---

## 🎯 Этап 1: Подготовка на стороне Timeweb

### 1.1 Настройка VPS на Timeweb
- Создать новый VPS (минимум 512 MB RAM, рекомендуется 1 GB)
- Выбрать Ubuntu 20.04+ или аналогичную ОС
- Получить IP адрес нового сервера
- Настроить SSH доступ (создать SSH ключи)

### 1.2 Установка необходимого ПО на новом сервере
```bash
# Docker
sudo apt update
sudo apt install -y docker.io

# Docker Compose
sudo apt install -y docker-compose

# Git
sudo apt install -y git

# UFW (firewall)
sudo apt install -y ufw
```

### 1.3 Настройка firewall
```bash
# Открыть порты: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (приложение)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable
```

---

## 🌐 Этап 2: Настройка нового домена

### 2.1 Регистрация/настройка домена fsp.insflow.online
- Если домен insflow.online уже зарегистрирован - создать поддомен fsp
- Если нет - зарегистрировать домен

### 2.2 Настройка DNS записей
Создать A-записи, указывающие на IP нового сервера Timeweb:
```
Тип    Имя        Значение              TTL
A      fsp        IP_TIMEWEB_SERVER     300
```

### 2.3 Ожидание распространения DNS
- Подождать 1-24 часа для распространения DNS
- Проверить через `dig fsp.insflow.online` или dnschecker.org

```bash
# Проверка DNS
dig fsp.insflow.online A
ping fsp.insflow.online
```

---

## 📦 Этап 3: Подготовка кода и конфигурации

### 3.1 Обновить файлы конфигурации (локально или на GitHub)

**Файлы для изменения:**

#### 1. `.env` файл
Обновить:
```env
ALLOWED_HOSTS=fsp.insflow.online
```

#### 2. `nginx.conf`
Заменить все упоминания домена:
```nginx
# Было:
server_name fsp.onbr.site;
ssl_certificate /etc/letsencrypt/live/fsp.onbr.site/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/fsp.onbr.site/privkey.pem;

# Стало:
server_name fsp.insflow.online;
ssl_certificate /etc/letsencrypt/live/fsp.insflow.online/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/fsp.insflow.online/privkey.pem;
```

#### 3. `DOMAIN_SETUP.md`
Обновить документацию с новым доменом

#### 4. `README.md`
Обновить ссылки на домен (если есть)

#### 5. GitHub Actions (`.github/workflows/deploy.yml`)
Обновить secrets:
```
DO_HOST → TW_HOST (новый IP Timeweb)
DO_USERNAME → TW_USERNAME
DO_SSH_KEY → TW_SSH_KEY
DO_SSH_PASSPHRASE → TW_SSH_PASSPHRASE
DO_PORT → TW_PORT
ALLOWED_HOSTS=fsp.insflow.online
```

### 3.2 Создать новую ветку для миграции (опционально)
```bash
git checkout -b migration/timeweb-insflow
git add .
git commit -m "Подготовка к миграции на Timeweb с новым доменом"
git push origin migration/timeweb-insflow
```

---

## 🚀 Этап 4: Деплой на Timeweb

### 4.1 Клонирование проекта на новый сервер
```bash
# Подключиться к серверу Timeweb
ssh user@TIMEWEB_IP

# Клонировать проект
cd /opt
sudo git clone https://github.com/grigra27/fsp.git fair-sber-price
cd fair-sber-price
sudo chown -R $USER:$USER .
```

### 4.2 Настройка переменных окружения
```bash
cp .env.example .env
nano .env  # Отредактировать с новыми настройками
```

Пример `.env`:
```env
SECRET_KEY=your-new-secret-key-here
DEBUG=False
ALLOWED_HOSTS=fsp.insflow.online
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
SBER_STOCKS_QUANTITY=22586948000
CBR_BASE_URL=https://www.cbr.ru/banking_sector/credit/coinfo/f123/
CACHE_TIMEOUT=60
PORT=8000
WORKERS=2
```

### 4.3 Первый запуск без SSL
```bash
# Временно закомментировать SSL секции в nginx.conf
# Закомментировать строки с listen 443 ssl и все ssl_* директивы

# Запустить проект
docker-compose -f docker-compose.prod.yml up -d
```

### 4.4 Проверка работоспособности
```bash
# Проверить статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверить логи
docker logs fsp_web
docker logs fsp_telegram_bot
docker logs fsp_nginx

# Проверить доступность (через HTTP)
curl http://fsp.insflow.online/api/health/
curl http://TIMEWEB_IP:8000/api/health/
```

---

## 🔒 Этап 5: Настройка SSL сертификатов

### 5.1 Остановить nginx
```bash
docker-compose -f docker-compose.prod.yml stop nginx
```

### 5.2 Получить SSL сертификаты от Let's Encrypt
```bash
# Создать директорию для сертификатов
mkdir -p ssl_copy

# Получить сертификаты
docker run -it --rm \
  -v "$(pwd)/ssl_copy:/etc/letsencrypt" \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  -d fsp.insflow.online \
  --email your-email@example.com \
  --agree-tos --non-interactive
```

### 5.3 Обновить nginx.conf
Раскомментировать SSL секции с новым доменом:
```nginx
server {
    listen 443 ssl;
    server_name fsp.insflow.online;

    ssl_certificate /etc/letsencrypt/live/fsp.insflow.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fsp.insflow.online/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... остальная конфигурация
}
```

### 5.4 Перезапустить nginx
```bash
docker-compose -f docker-compose.prod.yml up -d nginx
```

### 5.5 Проверить HTTPS
```bash
curl https://fsp.insflow.online/api/health/
curl -I https://fsp.insflow.online/
```

---

## 🔄 Этап 6: Миграция данных (если требуется)

### 6.1 Экспорт данных с Digital Ocean
```bash
# На старом сервере Digital Ocean
ssh user@DO_IP
cd /opt/fair-sber-price

# Создать бэкап базы данных
docker exec fsp_web python manage.py dumpdata > backup.json

# Создать полный архив проекта
tar -czf fsp-backup-$(date +%Y%m%d).tar.gz \
  backup.json \
  fsp/db/db.sqlite3 \
  fsp/logs/ \
  .env

# Скачать backup на локальную машину
exit
scp user@DO_IP:/opt/fair-sber-price/backup.json ./
scp user@DO_IP:/opt/fair-sber-price/fsp-backup-*.tar.gz ./
```

### 6.2 Импорт данных на Timeweb
```bash
# Загрузить backup на новый сервер
scp ./backup.json user@TIMEWEB_IP:/opt/fair-sber-price/
scp ./fsp-backup-*.tar.gz user@TIMEWEB_IP:/opt/fair-sber-price/

# На новом сервере Timeweb
ssh user@TIMEWEB_IP
cd /opt/fair-sber-price

# Импортировать данные
docker exec fsp_web python manage.py loaddata backup.json

# Или восстановить из архива
tar -xzf fsp-backup-*.tar.gz
```

---

## 🤖 Этап 7: Обновление Telegram бота

### 7.1 Проверка работы бота
```bash
# Проверить логи бота
docker logs fsp_telegram_bot -f

# Проверить переменные окружения
docker exec fsp_telegram_bot env | grep TELEGRAM

# Отправить команду /start боту в Telegram
# Отправить команду /info боту в Telegram
```

### 7.2 Обновление webhook (если используется)
Если бот использует webhook вместо polling, обновить URL webhook на новый домен:
```bash
# Проверить текущий webhook
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

# Установить новый webhook (если используется)
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://fsp.insflow.online/telegram/webhook"
```

---

## ✅ Этап 8: Финальная проверка и переключение

### 8.1 Чек-лист проверки на Timeweb
- [ ] https://fsp.insflow.online открывается
- [ ] https://fsp.insflow.online/api/health/ возвращает OK
- [ ] https://fsp.insflow.online/api/current/ возвращает данные
- [ ] SSL сертификат валидный (зеленый замок)
- [ ] HTTP редирект на HTTPS работает
- [ ] Telegram бот отвечает на команды /start, /info, /help
- [ ] Все контейнеры работают (docker ps)
- [ ] Логи не показывают критических ошибок
- [ ] Статические файлы загружаются корректно
- [ ] Данные отображаются правильно

### 8.2 Команды для проверки
```bash
# Статус всех контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверка здоровья
curl https://fsp.insflow.online/api/health/

# Проверка API
curl https://fsp.insflow.online/api/current/

# Проверка редиректа HTTP -> HTTPS
curl -I http://fsp.insflow.online/

# Проверка SSL сертификата
openssl s_client -connect fsp.insflow.online:443 -servername fsp.insflow.online

# Просмотр логов
docker logs fsp_web --tail 50
docker logs fsp_telegram_bot --tail 50
docker logs fsp_nginx --tail 50
```

### 8.3 Параллельная работа (опционально)
Можно держать оба сервера работающими несколько дней для проверки:
- Старый сервер: fsp.onbr.site
- Новый сервер: fsp.insflow.online

### 8.4 Обновление внешних ссылок
- Обновить ссылки в документации
- Обновить ссылки в README
- Обновить описание Telegram бота (если там указан домен)
- Обновить закладки и внутренние документы

---

## 🗑️ Этап 9: Отключение старого сервера

### 9.1 Создать финальный бэкап на Digital Ocean
```bash
# На сервере Digital Ocean
ssh user@DO_IP
cd /opt/fair-sber-price

# Полный бэкап проекта
tar -czf fsp-final-backup-$(date +%Y%m%d).tar.gz \
  /opt/fair-sber-price \
  --exclude='*/venv/*' \
  --exclude='*/__pycache__/*' \
  --exclude='*/node_modules/*'

# Скачать финальный бэкап
exit
scp user@DO_IP:/opt/fair-sber-price/fsp-final-backup-*.tar.gz ./backup/
```

### 9.2 Остановить сервисы на Digital Ocean
```bash
# На сервере Digital Ocean
ssh user@DO_IP
cd /opt/fair-sber-price

# Остановить все контейнеры
docker-compose -f docker-compose.prod.yml down

# Проверить что все остановлено
docker ps
```

### 9.3 Удалить дроплет Digital Ocean (через несколько дней)
После полной уверенности в работе на Timeweb:
1. Зайти в панель Digital Ocean
2. Перейти в раздел Droplets
3. Выбрать дроплет с проектом
4. Нажать "Destroy" и подтвердить удаление

**⚠️ Важно**: Перед удалением убедитесь что:
- Все данные перенесены
- Новый сервер работает стабильно минимум 7 дней
- Созданы все необходимые бэкапы

---

## 📝 Этап 10: Настройка автоматического обновления SSL

### 10.1 Добавить cron задачу на Timeweb
```bash
# Открыть crontab
crontab -e

# Добавить строку для обновления сертификатов каждые 3 месяца в 3:00
0 3 1 */3 * cd /opt/fair-sber-price && docker run --rm -v "$(pwd)/ssl_copy:/etc/letsencrypt" -p 80:80 certbot/certbot renew --standalone --pre-hook "docker-compose -f docker-compose.prod.yml stop nginx" --post-hook "docker-compose -f docker-compose.prod.yml start nginx" >> /var/log/certbot-renew.log 2>&1
```

### 10.2 Проверка автоматического обновления
```bash
# Тестовый запуск обновления (dry-run)
docker run --rm \
  -v "$(pwd)/ssl_copy:/etc/letsencrypt" \
  certbot/certbot renew --dry-run

# Просмотр логов обновления
tail -f /var/log/certbot-renew.log
```

---

## 🔧 Дополнительные рекомендации

### Мониторинг
1. **Настроить мониторинг uptime**:
   - UptimeRobot (бесплатный)
   - Pingdom
   - StatusCake

2. **Настроить алерты**:
   - Email уведомления при падении сервиса
   - Telegram уведомления через бота
   - SMS алерты (опционально)

3. **Мониторинг ресурсов**:
```bash
# Установить htop для мониторинга
sudo apt install htop

# Мониторинг Docker контейнеров
docker stats

# Мониторинг дискового пространства
df -h

# Мониторинг памяти
free -h
```

### Бэкапы
1. **Настроить регулярные бэкапы базы данных**:
```bash
# Создать скрипт бэкапа
cat > /opt/fair-sber-price/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/fsp"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Бэкап базы данных
docker exec fsp_web python manage.py dumpdata > $BACKUP_DIR/db_$DATE.json

# Бэкап SQLite файла
cp /opt/fair-sber-price/fsp/db/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# Удалить старые бэкапы (старше 30 дней)
find $BACKUP_DIR -name "*.json" -mtime +30 -delete
find $BACKUP_DIR -name "*.sqlite3" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/fair-sber-price/scripts/backup.sh

# Добавить в crontab (каждый день в 2:00)
crontab -e
# Добавить строку:
0 2 * * * /opt/fair-sber-price/scripts/backup.sh >> /var/log/fsp-backup.log 2>&1
```

2. **Настроить бэкап конфигурационных файлов**:
```bash
# Бэкап конфигурации
tar -czf /opt/backups/fsp/config_$(date +%Y%m%d).tar.gz \
  /opt/fair-sber-price/.env \
  /opt/fair-sber-price/nginx.conf \
  /opt/fair-sber-price/docker-compose.prod.yml
```

### Документация
1. **Обновить всю документацию**:
   - README.md
   - DOCUMENTATION.md
   - DOMAIN_SETUP.md
   - Этот файл (MIGRATION_PLAN.md)

2. **Создать runbook для типичных операций**:
   - Перезапуск сервисов
   - Просмотр логов
   - Обновление кода
   - Восстановление из бэкапа

### Оптимизация
1. **Настроить логротацию**:
```bash
# Создать конфигурацию logrotate
sudo cat > /etc/logrotate.d/fsp << 'EOF'
/opt/fair-sber-price/fsp/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

2. **Мониторинг производительности**:
```bash
# Установить инструменты мониторинга
sudo apt install -y sysstat iotop nethogs

# Просмотр статистики
iostat -x 1
iotop
nethogs
```

---

## ⚠️ Возможные проблемы и решения

### 1. DNS не распространился
**Симптомы**: Домен не открывается или открывается старый сервер

**Решения**:
```bash
# Проверить DNS
dig fsp.insflow.online A
nslookup fsp.insflow.online

# Проверить через онлайн сервисы
# https://dnschecker.org/
# https://www.whatsmydns.net/

# Очистить локальный DNS кеш
# macOS:
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

# Linux:
sudo systemd-resolve --flush-caches

# Windows:
ipconfig /flushdns
```

**Время ожидания**: До 24 часов, обычно 1-4 часа

### 2. SSL сертификат не получается
**Симптомы**: Ошибка при получении сертификата от Let's Encrypt

**Решения**:
```bash
# Проверить что порт 80 открыт
sudo ufw status
sudo netstat -tulpn | grep :80

# Убедиться что nginx остановлен
docker-compose -f docker-compose.prod.yml stop nginx
docker ps | grep nginx

# Проверить что домен указывает на правильный IP
dig fsp.insflow.online A

# Попробовать получить сертификат с подробными логами
docker run -it --rm \
  -v "$(pwd)/ssl_copy:/etc/letsencrypt" \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  -d fsp.insflow.online \
  --email your-email@example.com \
  --agree-tos --non-interactive \
  --verbose
```

### 3. Контейнеры не запускаются
**Симптомы**: Ошибки при запуске docker-compose

**Решения**:
```bash
# Проверить логи
docker-compose -f docker-compose.prod.yml logs

# Проверить конфигурацию
docker-compose -f docker-compose.prod.yml config

# Проверить образы
docker images

# Пересобрать образы
docker-compose -f docker-compose.prod.yml build --no-cache

# Очистить старые контейнеры и образы
docker system prune -a

# Проверить права доступа
ls -la fsp/db/
ls -la fsp/logs/
sudo chown -R 1000:1000 fsp/db fsp/logs
```

### 4. Telegram бот не работает
**Симптомы**: Бот не отвечает на команды

**Решения**:
```bash
# Проверить логи бота
docker logs fsp_telegram_bot -f

# Проверить переменные окружения
docker exec fsp_telegram_bot env | grep TELEGRAM

# Проверить токен бота
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Перезапустить бота
docker-compose -f docker-compose.prod.yml restart telegram-bot

# Проверить что контейнер запущен
docker ps | grep telegram

# Проверить сетевое подключение
docker exec fsp_telegram_bot ping -c 3 api.telegram.org
```

### 5. 502 Bad Gateway
**Симптомы**: Nginx возвращает 502 ошибку

**Решения**:
```bash
# Проверить что web контейнер запущен
docker ps | grep fsp_web

# Проверить логи web контейнера
docker logs fsp_web

# Проверить что порт 8000 слушается
docker exec fsp_web netstat -tulpn | grep 8000

# Проверить сетевое подключение между контейнерами
docker exec fsp_nginx ping -c 3 web

# Проверить конфигурацию nginx
docker exec fsp_nginx nginx -t

# Перезапустить сервисы
docker-compose -f docker-compose.prod.yml restart
```

### 6. Статические файлы не загружаются
**Симптомы**: CSS/JS файлы возвращают 404

**Решения**:
```bash
# Собрать статические файлы
docker exec fsp_web python manage.py collectstatic --noinput

# Проверить права доступа
docker exec fsp_web ls -la /app/staticfiles/

# Проверить volume в docker-compose
docker volume ls
docker volume inspect fair_sber_price_static_files

# Проверить конфигурацию nginx для статики
docker exec fsp_nginx cat /etc/nginx/nginx.conf | grep static
```

### 7. Высокое использование ресурсов
**Симптомы**: Сервер тормозит, высокая нагрузка

**Решения**:
```bash
# Проверить использование ресурсов
docker stats

# Проверить логи на ошибки
docker logs fsp_web | grep -i error
docker logs fsp_telegram_bot | grep -i error

# Ограничить ресурсы контейнеров в docker-compose.prod.yml
# Добавить в каждый сервис:
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 256M
    reservations:
      memory: 128M

# Перезапустить с новыми лимитами
docker-compose -f docker-compose.prod.yml up -d
```

### 8. База данных повреждена
**Симптомы**: Ошибки при работе с БД

**Решения**:
```bash
# Проверить целостность SQLite
docker exec fsp_web sqlite3 /app/db/db.sqlite3 "PRAGMA integrity_check;"

# Восстановить из бэкапа
docker exec fsp_web python manage.py loaddata /path/to/backup.json

# Пересоздать базу данных (ВНИМАНИЕ: потеря данных!)
docker exec fsp_web python manage.py migrate --run-syncdb
```

---

## 📞 Контакты и поддержка

### Полезные ссылки
- **Документация проекта**: README.md, DOCUMENTATION.md
- **Timeweb поддержка**: https://timeweb.com/ru/help/
- **Let's Encrypt документация**: https://letsencrypt.org/docs/
- **Docker документация**: https://docs.docker.com/

### Чек-лист после миграции
- [ ] Все сервисы работают на Timeweb
- [ ] SSL сертификаты настроены и работают
- [ ] Telegram бот отвечает на команды
- [ ] Данные перенесены корректно
- [ ] Настроены автоматические бэкапы
- [ ] Настроено автообновление SSL
- [ ] Обновлена вся документация
- [ ] Настроен мониторинг uptime
- [ ] Старый сервер отключен
- [ ] Созданы финальные бэкапы

---

**Дата создания плана**: 30 января 2026  
**Версия**: 1.0  
**Статус**: Готов к выполнению
