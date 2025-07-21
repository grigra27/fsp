# 🚀 Быстрый старт Fair Sber Price

## 💻 Локальная разработка

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
./scripts/start_dev.sh
```

Откройте: `http://localhost:8000`

## 🐳 Docker (локальный тест продакшена)

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

## ☁️ Деплой на DigitalOcean

### Автоматический деплой (рекомендуется)

1. **Fork репозитория** на GitHub
2. **Создайте DigitalOcean droplet** (Ubuntu 22.04, минимум 1GB RAM, Docker обычно уже установлен)
3. **Настройте GitHub Secrets**:
   ```
   DO_HOST=your-server-ip
   DO_USERNAME=root
   DO_SSH_KEY=your-private-ssh-key
   SECRET_KEY=your-secure-secret-key
   ALLOWED_HOSTS=your-domain.com,your-server-ip
   TELEGRAM_BOT_TOKEN=your-bot-token
   ```
4. **Запустите setup на сервере**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/grigra27/fair_sber_price/main/scripts/setup-server.sh | bash
   ```
5. **Push в main ветку** → автоматический деплой!

### Результат:
- 🌐 Веб-сайт: `http://fsp.hopto.org`
- 🤖 Telegram бот: работает автоматически
- 📊 API: `http://fsp.hopto.org/api/health/`
- 🔧 Админка: `http://fsp.hopto.org/admin/`

## 📋 Обязательные переменные окружения

```env
SECRET_KEY=your-very-secure-secret-key-50-chars-minimum
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DEBUG=False  # для продакшена
```

## 🔧 Полезные команды

```bash
# Проверка статуса (на сервере)
systemctl status fair-sber-price
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f telegram-bot

# Обновление (автоматически через GitHub)
git push origin main

# Ручное обновление (на сервере)
cd /opt/fair-sber-price
git pull && docker-compose -f docker-compose.prod.yml up -d
```

## 📖 Подробная документация

- **[README.md](README.md)** - полная документация проекта
- **[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)** - детальное руководство по деплою
- **[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)** - управление в продакшене
- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** - что было оптимизировано

## 🆘 Помощь

Если что-то не работает:
1. Проверьте логи: `docker-compose logs`
2. Health check: `curl http://localhost/api/health/`
3. Создайте Issue в GitHub