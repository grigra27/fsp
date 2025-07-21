#!/bin/bash

echo "🔍 Диагностика Telegram бота..."
echo "================================"

# Переходим в правильную директорию
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "📁 Переход в директорию проекта..."
    cd /opt/fair-sber-price 2>/dev/null || {
        echo "❌ Не удалось найти директорию проекта!"
        echo "Убедитесь, что вы находитесь в /opt/fair-sber-price"
        exit 1
    }
fi

# Проверяем статус контейнеров
echo "📊 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🔍 Детальная информация о боте:"
docker inspect fsp_telegram_bot --format='{{.State.Status}}: {{.State.Error}}'

echo ""
echo "📋 Последние логи бота:"
docker logs fsp_telegram_bot --tail=50

echo ""
echo "🔍 Проверка переменных окружения бота:"
docker exec fsp_telegram_bot env | grep -E "(TELEGRAM_BOT_TOKEN|DJANGO_SETTINGS_MODULE|SECRET_KEY)" | sed 's/=.*/=***/'

echo ""
echo "🔍 Проверка доступности базы данных:"
docker exec fsp_telegram_bot python manage.py check

echo ""
echo "🔍 Проверка Django приложений:"
docker exec fsp_telegram_bot python manage.py showmigrations

echo ""
echo "🔍 Тест подключения к Redis:"
docker exec fsp_redis redis-cli ping

echo ""
echo "🔍 Проверка сетевого подключения:"
docker exec fsp_telegram_bot ping -c 3 redis

echo ""
echo "================================"
echo "✅ Диагностика завершена!"