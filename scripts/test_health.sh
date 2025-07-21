#!/bin/bash

echo "🏥 Тестирование health check..."
echo "=============================="

# Проверяем статус контейнеров
echo "📊 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🔍 Проверка health check веб-приложения:"

# Получаем IP адрес сервера
SERVER_IP=$(hostname -I | awk '{print $1}')

# Тестируем health check изнутри контейнера
echo "1. Тест изнутри контейнера:"
docker exec fsp_web curl -f http://localhost:8000/api/health/ 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Health check внутри контейнера: OK"
else
    echo "❌ Health check внутри контейнера: FAILED"
    echo "Логи контейнера:"
    docker logs fsp_web --tail=10
fi

echo ""
echo "2. Тест с хоста:"
curl -f http://localhost:8000/api/health/ 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Health check с хоста: OK"
else
    echo "❌ Health check с хоста: FAILED"
fi

echo ""
echo "3. Тест с внешнего IP:"
curl -f http://$SERVER_IP:8000/api/health/ 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Health check с внешнего IP: OK"
else
    echo "❌ Health check с внешнего IP: FAILED"
fi

echo ""
echo "🔍 Детальная информация о health check:"
curl -s http://localhost:8000/api/health/ | python3 -m json.tool 2>/dev/null || echo "Не удалось получить JSON ответ"

echo ""
echo "🔍 Проверка основной страницы:"
curl -I http://localhost:8000/ 2>/dev/null | head -1

echo ""
echo "🔍 Проверка Docker health status:"
docker inspect fsp_web --format='{{.State.Health.Status}}'

echo ""
echo "🔍 История health checks:"
docker inspect fsp_web --format='{{range .State.Health.Log}}{{.Start}} - {{.Output}}{{end}}' | tail -5

echo ""
echo "=============================="
echo "✅ Тестирование завершено!"