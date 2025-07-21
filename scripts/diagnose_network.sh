#!/bin/bash

echo "🌐 Диагностика сетевых проблем..."
echo "================================="

# Получаем информацию о сервере
SERVER_IP=$(hostname -I | awk '{print $1}')
DOMAIN="fsp.hopto.org"

echo "🖥️ Информация о сервере:"
echo "IP адрес: $SERVER_IP"
echo "Домен: $DOMAIN"

echo ""
echo "🔍 Проверка DNS резолюции:"
nslookup $DOMAIN || echo "❌ DNS резолюция не работает"
dig $DOMAIN A +short || echo "❌ dig команда недоступна"

echo ""
echo "🔍 Проверка портов:"
echo "Порт 8000 (приложение):"
netstat -tlnp | grep :8000 || ss -tlnp | grep :8000 || echo "❌ Порт 8000 не слушается"

echo "Порт 80 (HTTP):"
netstat -tlnp | grep :80 || ss -tlnp | grep :80 || echo "ℹ️ Порт 80 не используется"

echo "Порт 443 (HTTPS):"
netstat -tlnp | grep :443 || ss -tlnp | grep :443 || echo "ℹ️ Порт 443 не используется"

echo ""
echo "🔥 Проверка файрвола (UFW):"
if command -v ufw &> /dev/null; then
    ufw status
else
    echo "ℹ️ UFW не установлен"
fi

echo ""
echo "🔥 Проверка iptables:"
iptables -L INPUT -n | grep -E "(8000|80|443)" || echo "ℹ️ Нет специальных правил для веб-портов"

echo ""
echo "🔍 Тест подключения к приложению:"
echo "1. Локальный тест:"
curl -I http://localhost:8000/ 2>/dev/null && echo "✅ Localhost работает" || echo "❌ Localhost не работает"

echo "2. Тест по IP:"
curl -I http://$SERVER_IP:8000/ 2>/dev/null && echo "✅ IP подключение работает" || echo "❌ IP подключение не работает"

echo "3. Тест по домену (если DNS работает):"
if nslookup $DOMAIN > /dev/null 2>&1; then
    curl -I http://$DOMAIN:8000/ 2>/dev/null && echo "✅ Домен работает" || echo "❌ Домен не работает"
else
    echo "⏭️ Пропускаем тест домена (DNS не работает)"
fi

echo ""
echo "🔍 Проверка ALLOWED_HOSTS в приложении:"
cd /opt/fair-sber-price
if [ -f .env ]; then
    echo "ALLOWED_HOSTS из .env:"
    grep ALLOWED_HOSTS .env || echo "❌ ALLOWED_HOSTS не найден в .env"
else
    echo "❌ Файл .env не найден"
fi

echo ""
echo "🔍 Проверка контейнера:"
docker-compose -f docker-compose.prod.yml ps web

echo ""
echo "🔍 Проверка логов nginx (если используется):"
docker logs fsp_nginx --tail=10 2>/dev/null || echo "ℹ️ Nginx контейнер не запущен"

echo ""
echo "================================="
echo "✅ Диагностика завершена!"
echo ""
echo "📝 Рекомендации:"
echo "1. Если localhost работает, но IP/домен нет - проблема с файрволом"
echo "2. Если DNS не работает - обновите настройки домена"
echo "3. Если порт 8000 не слушается - проблема с контейнером"
echo "4. Проверьте ALLOWED_HOSTS в .env файле"