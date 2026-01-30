#!/bin/bash
# Fix deployment issues for Fair Sber Price

set -e

echo "=== Fair Sber Price Deployment Fix ==="
echo ""

# Stop containers
echo "1. Stopping containers..."
docker-compose -f docker-compose.prod.yml down

# Create and fix database directory permissions
echo "2. Setting up database directory..."
mkdir -p fsp/db
chmod 777 fsp/db

# Remove old database if it exists (fresh start)
if [ -f fsp/db/db.sqlite3 ]; then
    echo "   Backing up old database..."
    mv fsp/db/db.sqlite3 fsp/db/db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
fi

# Create logs directory
echo "3. Setting up logs directory..."
mkdir -p fsp/logs
chmod 777 fsp/logs

# Pull latest images
echo "4. Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Start web service first to initialize database
echo "5. Starting web service to initialize database..."
docker-compose -f docker-compose.prod.yml up -d web

# Wait for web service to be ready
echo "6. Waiting for web service to initialize..."
sleep 10

# Run migrations
echo "7. Running database migrations..."
docker exec fsp_web python manage.py migrate

# Collect static files
echo "8. Collecting static files..."
docker exec fsp_web python manage.py collectstatic --noinput

# Fix database permissions again (after creation)
echo "9. Fixing database permissions..."
chmod 666 fsp/db/db.sqlite3 2>/dev/null || true

# Start all services
echo "10. Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Show status
echo ""
echo "=== Deployment Status ==="
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "=== Checking logs ==="
echo "Web service logs:"
docker logs fsp_web --tail 20

echo ""
echo "Telegram bot logs:"
docker logs fsp_telegram_bot --tail 20

echo ""
echo "Nginx logs:"
docker logs fsp_nginx --tail 20

echo ""
echo "=== Setup Complete ==="
echo "Your application should now be running on http://fsp.tw1.ru"
echo ""
echo "To add SSL later, follow these steps:"
echo "1. Install certbot on the host"
echo "2. Run: certbot certonly --standalone -d fsp.tw1.ru"
echo "3. Copy certificates: mkdir -p ssl_copy && cp -r /etc/letsencrypt/* ssl_copy/"
echo "4. Update docker-compose.prod.yml to use nginx.conf instead of nginx.conf.nossl"
echo "5. Restart: docker-compose -f docker-compose.prod.yml restart nginx"
