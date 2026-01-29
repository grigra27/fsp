#!/bin/bash

echo "=== Fair Sber Price Diagnostics ==="
echo ""

cd /opt/fair-sber-price

echo "1. Container Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""

echo "2. Testing web service directly (bypass nginx):"
curl -s http://localhost:8000/ | head -20
echo ""

echo "3. Testing health endpoint:"
curl -s http://localhost:8000/api/health/ | jq .
echo ""

echo "4. Checking web logs (last 30 lines):"
docker-compose -f docker-compose.prod.yml logs --tail=30 web
echo ""

echo "5. Checking nginx logs (last 20 lines):"
docker-compose -f docker-compose.prod.yml logs --tail=20 nginx
echo ""

echo "6. Environment variables in web container:"
docker-compose -f docker-compose.prod.yml exec -T web env | grep -E "ALLOWED_HOSTS|DEBUG|SECRET_KEY" | sed 's/SECRET_KEY=.*/SECRET_KEY=***/'
echo ""

echo "=== End of Diagnostics ==="
