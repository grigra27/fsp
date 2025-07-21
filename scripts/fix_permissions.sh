#!/bin/bash

echo "🔧 Исправление прав доступа для контейнеров..."
echo "=============================================="

# Переходим в директорию проекта
cd /opt/fair-sber-price

# Останавливаем все контейнеры
echo "🛑 Остановка контейнеров..."
docker-compose -f docker-compose.prod.yml down

# Создаем необходимые директории с правильными правами
echo "📁 Создание директорий с правильными правами..."
mkdir -p fsp/logs
mkdir -p fsp/staticfiles
chmod 755 fsp/logs
chmod 755 fsp/staticfiles

# Создаем базу данных если её нет
echo "🗄️ Проверка базы данных..."
if [ ! -f "fsp/db.sqlite3" ]; then
    echo "📝 Создание базы данных..."
    touch fsp/db.sqlite3
fi
chmod 664 fsp/db.sqlite3

# Устанавливаем правильные права на все файлы проекта
echo "🔐 Установка прав доступа..."
chown -R 1000:1000 fsp/
find fsp/ -type d -exec chmod 755 {} \;
find fsp/ -type f -exec chmod 644 {} \;
chmod 664 fsp/db.sqlite3
chmod 755 fsp/logs
chmod 755 fsp/staticfiles

# Обновляем образы
echo "📥 Обновление Docker образов..."
docker pull ghcr.io/grigra27/fair_sber_price-web:latest
docker pull ghcr.io/grigra27/fair_sber_price-bot:latest

# Запускаем контейнеры
echo "🚀 Запуск контейнеров..."
docker-compose -f docker-compose.prod.yml up -d

# Ждем запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 30

# Проверяем статус
echo "📊 Проверка статуса контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📋 Логи веб-приложения:"
docker logs fsp_web --tail=10

echo ""
echo "📋 Логи Telegram бота:"
docker logs fsp_telegram_bot --tail=10

echo ""
echo "✅ Исправление прав доступа завершено!"
echo "🌐 Проверьте приложение: http://$(hostname -I | awk '{print $1}'):8000"