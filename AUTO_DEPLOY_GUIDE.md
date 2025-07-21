# 🚀 Автоматический деплой Fair Sber Price

## ✨ Полностью автоматический деплой без ручной настройки сервера!

GitHub Actions автоматически настроит сервер и развернет приложение. Никаких скриптов запускать не нужно!

## 📋 Что нужно сделать:

### 1. Создайте DigitalOcean Droplet
- **OS**: Ubuntu 22.04 LTS
- **Size**: минимум 1GB RAM (рекомендуется 2GB)
- **Дополнительно**: Docker должен быть установлен (обычно уже есть)

### 2. Настройте GitHub Secrets

В настройках вашего GitHub репозитория (`Settings` → `Secrets and variables` → `Actions`) добавьте:

```
DO_HOST=your-server-ip-address
DO_USERNAME=root
DO_SSH_KEY=your-private-ssh-key
DO_PORT=22
SECRET_KEY=your-very-secure-secret-key-50-characters-minimum
ALLOWED_HOSTS=your-domain.com,your-server-ip
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

#### Как получить SSH ключ:
```bash
# На вашем компьютере:
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
cat ~/.ssh/id_rsa.pub  # Добавьте в DigitalOcean
cat ~/.ssh/id_rsa      # Добавьте в GitHub Secret DO_SSH_KEY
```

### 3. Деплой
```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

**Всё! 🎉**

## 🔄 Что происходит автоматически:

### При каждом push в main ветку:

1. **🧪 Тестирование** - проверка кода
2. **🏗️ Сборка Docker образов** - web и bot
3. **📦 Публикация** в GitHub Container Registry
4. **🚀 Автоматическая настройка сервера:**
   - Установка Docker Compose (если нужно)
   - Создание папок и файлов конфигурации
   - Настройка firewall
   - Создание systemd сервисов
5. **📥 Загрузка** новых Docker образов
6. **🔄 Перезапуск** всех сервисов
7. **🏥 Проверка** работоспособности

## 🎯 Результат деплоя:

После успешного деплоя у вас будет работать:

- **🌐 Веб-сайт**: `http://your-server-ip:8000`
- **🤖 Telegram бот**: автоматически работает
- **📊 API**: `http://your-server-ip:8000/api/health/`
- **🔧 Админка**: `http://your-server-ip:8000/admin/`

## 📊 Мониторинг и управление:

### Проверка статуса (SSH на сервер):
```bash
# Статус сервисов
systemctl status fair-sber-price
docker-compose -f /opt/fair-sber-price/docker-compose.prod.yml ps

# Логи
cd /opt/fair-sber-price
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f telegram-bot

# Перезапуск
systemctl restart fair-sber-price
```

### Обновление:
Просто сделайте push в main ветку - всё обновится автоматически!

## 🔧 Архитектура:

```
┌─────────────────────────────────────────┐
│           DigitalOcean Server           │
├─────────────────────────────────────────┤
│  🐳 Docker Containers:                  │
│  ┌─────────────────────────────────────┐ │
│  │  📦 Redis (Cache)                   │ │
│  │  🌐 Django Web App (Port 8000)     │ │
│  │  🤖 Telegram Bot                    │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  📁 Files:                              │
│  ├── /opt/fair-sber-price/             │
│  │   ├── docker-compose.prod.yml       │
│  │   ├── .env                          │
│  │   └── fsp/                          │
│  │       ├── logs/                     │
│  │       └── db.sqlite3                │
│  └── /etc/systemd/system/              │
│      └── fair-sber-price.service       │
└─────────────────────────────────────────┘
```

## 🚨 Устранение неполадок:

### Если деплой не удался:
1. Проверьте GitHub Actions логи
2. Убедитесь, что все Secrets настроены правильно
3. Проверьте SSH доступ к серверу
4. Убедитесь, что Docker установлен на сервере

### Если сайт не открывается:
```bash
# SSH на сервер и проверьте:
cd /opt/fair-sber-price
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs web
```

### Если Telegram бот не работает:
```bash
# Проверьте логи бота:
docker-compose -f docker-compose.prod.yml logs telegram-bot
```

## 🎉 Преимущества автоматического деплоя:

- ✅ **Нулевая настройка** - никаких скриптов не нужно запускать
- ✅ **Идемпотентность** - можно запускать много раз безопасно
- ✅ **Автоматические обновления** - push = деплой
- ✅ **Откат** - просто откатите commit и push
- ✅ **Мониторинг** - встроенные health checks
- ✅ **Безопасность** - все секреты в GitHub Secrets

## 🔄 Workflow:

1. **Разработка** → commit → push
2. **GitHub Actions** → автоматический деплой
3. **Готово!** 🚀

Больше никаких ручных настроек сервера! 🎉