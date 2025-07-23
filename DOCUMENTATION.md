# Fair Sber Price - Полная документация 📚

## 📋 Содержание
1. [Структура проекта](#структура-проекта)
2. [Быстрый старт](#быстрый-старт)
3. [Деплой в продакшн](#деплой-в-продакшн)
4. [Настройка HTTPS](#настройка-https)
5. [Устранение проблем](#устранение-проблем)
6. [Безопасность](#безопасность)
7. [Управление проектом](#управление-проектом)
8. [Конфигурация](#конфигурация)

## �  Быстрый старт

### 💻 Локальная разработка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/grigra27/fair_sber_price.git
cd fair_sber_price

# 2. Настройте окружение
cd fsp
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 3. Настройте переменные
cp ../.env.example ../.env
# Отредактируйте .env файл

# 4. Запустите проект
python manage.py migrate
python manage.py runserver
```

Откройте: `http://localhost:8000`

### 🐳 Docker (локальный тест продакшена)

```bash
# 1. Настройте переменные
cp .env.example .env
# Отредактируйте .env файл

# 2. Запустите все сервисы
docker-compose -f docker-compose.prod.yml up -d

# 3. Проверьте статус
docker-compose -f docker-compose.prod.yml ps
curl http://localhost/api/health/
```

## 📁 Структура проекта

```
fair_sber_price/
├── 📄 README.md                    # Основная документация
├── 📄 DOCUMENTATION.md             # Расширенная документация
├── 📄 .env.example                 # Пример переменных окружения
├── 📄 docker-compose.prod.yml      # Docker Compose для продакшена
├── 📄 Dockerfile.web               # Docker образ веб-приложения
├── 📄 Dockerfile.bot               # Docker образ Telegram бота
├── 📄 nginx.conf                   # Конфигурация Nginx
│
├── 📁 fsp/                         # Django приложение
│   ├── 📄 manage.py                # Django management
│   ├── 📄 requirements.txt         # Python зависимости
│   ├── 📄 requirements-prod.txt    # Продакшен зависимости
│   ├── 📄 db.sqlite3               # База данных SQLite
│   │
│   ├── 📁 fsp/                     # Основные настройки Django
│   │   ├── 📄 settings.py          # Базовые настройки
│   │   ├── 📄 production.py        # Продакшен настройки
│   │   ├── 📄 urls.py              # URL маршруты
│   │   └── 📄 wsgi.py              # WSGI конфигурация
│   │
│   ├── 📁 price/                   # Основное приложение
│   │   ├── 📄 models.py            # Модели данных
│   │   ├── 📄 views.py             # Представления
│   │   ├── 📄 urls.py              # URL маршруты
│   │   ├── 📄 services.py          # Бизнес-логика
│   │   └── 📁 management/commands/ # Django команды
│   │
│   ├── 📁 telegrambot/             # Telegram бот
│   │   ├── 📄 bot.py               # Основной код бота
│   │   └── 📁 management/commands/ # Команды бота
│   │
│   ├── 📁 templates/               # HTML шаблоны
│   │   ├── 📄 base.html            # Базовый шаблон
│   │   ├── 📄 index.html           # Главная страница
│   │   └── 📁 includes/            # Компоненты шаблонов
│   │
│   ├── 📁 static_dev/              # Статические файлы разработки
│   ├── 📁 staticfiles/             # Собранные статические файлы
│   └── 📁 logs/                    # Логи приложения
│
├── 📁 scripts/                     # Скрипты управления
│   └── 📄 fsp_manager.sh           # Универсальный скрипт управления
│
└── 📁 .github/workflows/           # GitHub Actions
    └── 📄 deploy.yml               # Автоматический деплой
```

## 🚀 Деплой в продакшн

### Требования к серверу
- Ubuntu 20.04+ или аналогичный
- Docker и Docker Compose
- Открытые порты: 22, 80, 443, 8000

### Автоматический деплой через GitHub Actions
1. **Настройте GitHub Secrets** в репозитории:
   ```
   DO_HOST=your-server-ip
   DO_USERNAME=root
   DO_SSH_KEY=your-private-ssh-key
   DO_SSH_PASSPHRASE=your-ssh-key-password
   DO_PORT=22
   SECRET_KEY=your-django-secret-key
   ALLOWED_HOSTS=your-domain.com,your-server-ip,localhost
   TELEGRAM_BOT_TOKEN=your-bot-token
   ```

2. **Сделайте push в main ветку**:
   ```bash
   git push origin main
   ```

3. **GitHub Actions автоматически**:
   - Соберет Docker образы
   - Настроит сервер
   - Запустит приложение

### Ручной деплой
```bash
# На сервере
cd /opt
git clone https://github.com/grigra27/fsp.git fair-sber-price
cd fair-sber-price

# Создание .env файла
cp .env.example .env
# Отредактируйте .env с вашими настройками

# Запуск деплоя
./scripts/fsp_manager.sh deploy
```

### Чек-лист деплоя
1. ✅ Настроены переменные окружения в `.env`
2. ✅ Открыты необходимые порты (80, 443, 8000)
3. ✅ Настроен домен (A-запись указывает на IP сервера)
4. ✅ Установлены Docker и Docker Compose
5. ✅ Запущены все контейнеры
6. ✅ Настроен SSL (если требуется)
7. ✅ Проверен health check (`/api/health/`)
8. ✅ Проверен Telegram бот

## 🔒 Настройка HTTPS

### Настройка с Let's Encrypt
1. **Подготовка**:
   ```bash
   # Создайте директорию для сертификатов
   mkdir -p ssl/certbot/conf ssl/certbot/www
   ```

2. **Получение сертификатов**:
   ```bash
   # Запустите certbot в Docker
   docker run -it --rm \
     -v "$(pwd)/ssl/certbot/conf:/etc/letsencrypt" \
     -v "$(pwd)/ssl/certbot/www:/var/www/certbot" \
     -p 80:80 \
     certbot/certbot certonly --standalone \
     -d your-domain.com --email your-email@example.com --agree-tos
   ```

3. **Настройка Nginx**:
   Конфигурация уже включена в `nginx.conf`. Убедитесь, что пути к сертификатам правильные:
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
       
       # Остальные настройки...
   }
   ```

4. **Обновление docker-compose.prod.yml**:
   ```yaml
   nginx:
     volumes:
       - ./ssl/certbot/conf:/etc/letsencrypt
       - ./ssl/certbot/www:/var/www/certbot
   ```

5. **Перезапуск Nginx**:
   ```bash
   ./scripts/fsp_manager.sh restart
   ```

### Автоматическое обновление сертификатов
Добавьте в crontab:
```bash
0 3 * * * cd /opt/fair-sber-price && docker run --rm -v "$(pwd)/ssl/certbot/conf:/etc/letsencrypt" -v "$(pwd)/ssl/certbot/www:/var/www/certbot" certbot/certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx
```

## 🔧 Устранение проблем

### Частые проблемы и решения

#### 1. 404 на главной странице
**Причина**: HTTPS редирект или проблемы с ALLOWED_HOSTS
**Решение**: 
```bash
./scripts/fsp_manager.sh fix
```

#### 2. Проблемы с базой данных
**Причина**: Неправильная конфигурация PostgreSQL или проблемы с подключением
**Решение**: 
```bash
# Проверка статуса PostgreSQL
docker-compose -f docker-compose.prod.yml ps postgres
docker logs fsp_postgres

# Проверка подключения к базе данных
docker exec -it fsp_postgres psql -U fsp_user -d fsp_db -c "SELECT 1;"

# Если нужно пересоздать базу данных
docker-compose -f docker-compose.prod.yml down
docker volume rm fair_sber_price_postgres_data
docker-compose -f docker-compose.prod.yml up -d
```

#### 3. Telegram бот не работает
**Причина**: Отсутствуют переменные окружения
**Решение**: 
```bash
# Проверка переменных окружения
grep TELEGRAM_BOT_TOKEN .env

# Диагностика бота
./scripts/fsp_manager.sh debug-bot

# Исправление проблем с ботом
./scripts/fsp_manager.sh fix-bot
```

#### 4. Nginx не работает
**Причина**: Конфликт с системным nginx
**Решение**: 
```bash
# Остановка системного nginx
systemctl stop nginx
systemctl disable nginx

# Диагностика и настройка nginx
./scripts/fsp_manager.sh nginx
```

### Диагностические команды

```bash
# Проверка статуса
./scripts/fsp_manager.sh status
./scripts/fsp_manager.sh health

# Просмотр логов
./scripts/fsp_manager.sh logs        # Все логи
./scripts/fsp_manager.sh logs web    # Только веб-приложение
./scripts/fsp_manager.sh logs bot    # Только Telegram бот

# Диагностика сети
./scripts/fsp_manager.sh debug-net

# Диагностика 404 ошибок
./scripts/fsp_manager.sh debug-404
```

## 🔒 Безопасность

### Основные меры безопасности
1. **Переменные окружения**:
   - Все секретные ключи хранятся в `.env` файле
   - Файл `.env` не включен в Git репозиторий
   - Используйте GitHub Secrets для CI/CD

2. **HTTPS**:
   - Настроено перенаправление с HTTP на HTTPS
   - Используются современные протоколы шифрования
   - Настроены HTTP Security Headers

3. **Доступ к серверу**:
   - Используйте SSH ключи вместо паролей
   - Отключите вход по паролю
   - Используйте нестандартный порт SSH

4. **Файрвол**:
   - Открыты только необходимые порты (22, 80, 443, 8000)
   - Используйте UFW для управления файрволом

5. **Обновления**:
   - Регулярно обновляйте Docker образы
   - Следите за обновлениями безопасности

### SSH Безопасность

#### Генерация безопасного SSH ключа:
```bash
# Рекомендуемый способ - ed25519 с паролем
ssh-keygen -t ed25519 -C "github-actions-deploy-$(date +%Y%m%d)"

# Альтернативный способ - RSA 4096 бит
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy-$(date +%Y%m%d)"

# ВАЖНО: При запросе passphrase введите НАДЕЖНЫЙ пароль!
```

#### Настройка сервера:
```bash
# Правильные права доступа
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/id_*

# Отключение входа по паролю (только ключи)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### Файрвол сервера:
```bash
# Настройка UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Приложение
sudo ufw --force enable
```

### Регулярное обслуживание

#### Каждые 3 месяца:
- Ротация SSH ключей
- Обновление SECRET_KEY
- Проверка логов безопасности
- Обновление системы сервера

#### Каждый месяц:
- Проверка активных SSH сессий
- Анализ логов доступа
- Обновление зависимостей

### Мониторинг безопасности

#### Логи для отслеживания:
- SSH подключения: `/var/log/auth.log`
- Приложение: `fsp/logs/app.log`
- Системные события: `/var/log/syslog`

#### Команды для проверки:
```bash
# Активные SSH сессии
who

# Последние входы
last

# Неудачные попытки входа
sudo grep "Failed password" /var/log/auth.log
```

## 🛠️ Управление проектом

### Универсальный скрипт управления
Все операции выполняются через единый скрипт `./scripts/fsp_manager.sh`:

```bash
# Основные команды
./scripts/fsp_manager.sh deploy    # Полный деплой
./scripts/fsp_manager.sh start     # Запуск сервисов
./scripts/fsp_manager.sh stop      # Остановка сервисов
./scripts/fsp_manager.sh restart   # Перезапуск сервисов
./scripts/fsp_manager.sh status    # Статус контейнеров
./scripts/fsp_manager.sh logs      # Просмотр логов

# Диагностика и исправление
./scripts/fsp_manager.sh health    # Проверка здоровья
./scripts/fsp_manager.sh fix       # Исправление проблем
./scripts/fsp_manager.sh fix-bot   # Исправление бота
./scripts/fsp_manager.sh fix-perms # Исправление прав доступа
./scripts/fsp_manager.sh debug-404 # Диагностика 404
./scripts/fsp_manager.sh debug-bot # Диагностика бота
./scripts/fsp_manager.sh debug-net # Диагностика сети

# Обслуживание
./scripts/fsp_manager.sh update    # Обновление образов
./scripts/fsp_manager.sh backup    # Резервное копирование
./scripts/fsp_manager.sh clean     # Очистка ресурсов
./scripts/fsp_manager.sh nginx     # Настройка Nginx
```

### Docker команды
```bash
# Запуск всех сервисов
docker-compose -f docker-compose.prod.yml up -d

# Остановка
docker-compose -f docker-compose.prod.yml down

# Просмотр логов
docker logs fsp_web
docker logs fsp_telegram_bot

# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps
```

### Переменные окружения (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-server-ip
TELEGRAM_BOT_TOKEN=your-bot-token
REDIS_URL=redis://redis:6379/0
POSTGRES_DB=fsp_db
POSTGRES_USER=fsp_user
POSTGRES_PASSWORD=your-secure-password
```

## 🔧 Конфигурация

### Docker сервисы
- **web**: Django приложение (порт 8000)
- **telegram-bot**: Telegram бот
- **redis**: Кеширование
- **nginx**: Reverse proxy (порт 80/443)

### Доступ к приложению
- **Веб-интерфейс**: http://your-domain.com/
- **API**: http://your-domain.com/api/
- **Health check**: http://your-domain.com/api/health/
- **Telegram бот**: https://t.me/fairbankprice_bot

### Временная зона
Приложение настроено на использование московского времени (Europe/Moscow) для всех дат и времени.

## ⚡ Оптимизация производительности

### Реализованные оптимизации
1. **Многоуровневое кеширование**:
   - Redis для кеширования данных API (MOEX, ЦБ РФ)
   - Кеширование на уровне Django views (15-300 секунд)
   - Кеширование полных данных в services (30 секунд)
   - Nginx кеширование для статических файлов и API

2. **Оптимизация базы данных**:
   - PostgreSQL с пулом соединений (CONN_MAX_AGE=60)
   - Индексы на часто используемых полях
   - Оптимизированные запросы

3. **Оптимизация веб-сервера**:
   - Gunicorn с оптимальным количеством воркеров
   - Nginx с keepalive соединениями
   - Gzip сжатие для всех текстовых ресурсов
   - HTTP/2 поддержка

4. **Оптимизация приложения**:
   - Уменьшен timeout API запросов до 5 секунд
   - Кеширование шаблонов Django
   - Отключена локализация для лучшей производительности
   - Оптимизированные HTTP заголовки

### Мониторинг производительности
```bash
# Проверка времени ответа
curl -w "@curl-format.txt" -o /dev/null -s http://your-domain.com/

# Мониторинг Redis
docker exec fsp_redis redis-cli info stats

# Мониторинг PostgreSQL
docker exec fsp_postgres pg_stat_activity

# Логи производительности Gunicorn
docker logs fsp_web | grep "access"
```

### Рекомендации по дальнейшей оптимизации
1. Настройте CDN для статических файлов
2. Используйте HTTP/2 Server Push для критических ресурсов
3. Настройте мониторинг производительности (например, New Relic)
4. Рассмотрите использование async views для Django

---

**Для получения дополнительной информации обратитесь к README.md**