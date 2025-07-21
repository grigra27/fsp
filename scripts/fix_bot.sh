#!/bin/bash

echo "🔧 Исправление проблем с Telegram ботом..."
echo "=========================================="

# Переходим в директорию проекта
cd /opt/fair-sber-price

# Останавливаем бота
echo "🛑 Остановка бота..."
docker-compose -f docker-compose.prod.yml stop telegram-bot

# Удаляем старый контейнер
echo "🗑️ Удаление старого контейнера..."
docker-compose -f docker-compose.prod.yml rm -f telegram-bot

# Обновляем образ бота
echo "📥 Обновление образа бота..."
docker pull ghcr.io/grigra27/fair_sber_price-bot:latest

# Проверяем переменные окружения
echo "🔍 Проверка переменных окружения..."
if [ -f .env ]; then
    source .env
fi

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

if [ -n "$missing_vars" ]; then
    echo "❌ Отсутствуют переменные окружения:$missing_vars"
    echo "Проверьте файл .env"
    exit 1
fi

echo "✅ Все необходимые переменные окружения найдены"

# Проверяем доступность базы данных
echo "🔍 Проверка базы данных..."
if [ ! -f "./fsp/db.sqlite3" ]; then
    echo "⚠️ База данных не найдена, создаем..."
    touch ./fsp/db.sqlite3
    chmod 664 ./fsp/db.sqlite3
fi

# Создаем директорию для логов если её нет
echo "📁 Создание директории для логов..."
mkdir -p ./fsp/logs
chmod 755 ./fsp/logs

# Запускаем бота
echo "🚀 Запуск бота..."
docker-compose -f docker-compose.prod.yml up -d telegram-bot

# Ждем запуска
echo "⏳ Ожидание запуска бота..."
sleep 10

# Проверяем статус
echo "📊 Проверка статуса бота..."
docker-compose -f docker-compose.prod.yml ps telegram-bot

# Показываем логи
echo "📋 Последние логи бота:"
docker logs fsp_telegram_bot --tail=20

echo ""
echo "✅ Исправление завершено!"
echo "Если бот все еще не работает, проверьте логи: docker logs fsp_telegram_bot"