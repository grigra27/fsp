#!/bin/bash

echo "🔍 Диагностика 404 ошибки на главной странице..."
echo "=============================================="

# Переходим в директорию проекта
cd /opt/fair-sber-price

echo "📊 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📋 Логи веб-приложения (последние 30 строк):"
docker logs fsp_web --tail=30

echo ""
echo "🔍 Тест главной страницы изнутри контейнера:"
docker exec fsp_web curl -I http://localhost:8000/ 2>/dev/null || echo "❌ Не удалось подключиться изнутри контейнера"

echo ""
echo "🔍 Тест с хоста:"
curl -I http://localhost:8000/ 2>/dev/null || echo "❌ Не удалось подключиться с хоста"

echo ""
echo "🔍 Проверка Django URL patterns:"
docker exec fsp_web python manage.py show_urls 2>/dev/null || echo "Команда show_urls недоступна"

echo ""
echo "🔍 Проверка Django приложений:"
docker exec fsp_web python manage.py check

echo ""
echo "🔍 Проверка статических файлов:"
docker exec fsp_web ls -la /app/staticfiles/ | head -10

echo ""
echo "🔍 Проверка шаблонов:"
docker exec fsp_web ls -la /app/templates/

echo ""
echo "🔍 Тест health endpoint:"
curl -s http://localhost:8000/api/health/ | python3 -m json.tool 2>/dev/null || echo "❌ Health endpoint недоступен"

echo ""
echo "🔍 Проверка переменных окружения:"
docker exec fsp_web env | grep -E "(DEBUG|ALLOWED_HOSTS|DJANGO_SETTINGS_MODULE)" | sed 's/=.*/=***/'

echo ""
echo "=============================================="
echo "✅ Диагностика завершена!"