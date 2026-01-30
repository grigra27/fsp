# Deployment Fix Guide

## Current Issues

Your deployment has three main problems:

1. **Nginx SSL certificates missing** - Nginx is looking for SSL certificates that don't exist
2. **Database permission issues** - Telegram bot can't access the SQLite database
3. **Health check failures** - Web service returns 503 because database isn't initialized

## Quick Fix

Run this command on your server:

```bash
cd /opt/fair-sber-price
bash scripts/fix_deployment.sh
```

This script will:
- Stop all containers
- Fix database and log directory permissions
- Initialize the database with migrations
- Collect static files
- Start all services without SSL (HTTP only)
- Show you the status

## Manual Fix (if you prefer)

```bash
# 1. Stop containers
docker-compose -f docker-compose.prod.yml down

# 2. Fix permissions
mkdir -p fsp/db fsp/logs
chmod 777 fsp/db fsp/logs

# 3. Start web service
docker-compose -f docker-compose.prod.yml up -d web

# 4. Initialize database
docker exec fsp_web python manage.py migrate
docker exec fsp_web python manage.py collectstatic --noinput

# 5. Fix database file permissions
chmod 666 fsp/db/db.sqlite3

# 6. Start all services
docker-compose -f docker-compose.prod.yml up -d
```

## What Changed

### docker-compose.prod.yml
- Removed `user: "1000:1000"` from telegram-bot (was causing permission issues)
- Changed nginx to use `nginx.conf.nossl` (HTTP only, no SSL)
- Removed port 443 and SSL certificate volume mount

### nginx.conf.nossl (new file)
- HTTP-only configuration
- No SSL certificate requirements
- Same proxy settings and optimizations

## Adding SSL Later

Once your app is running, you can add SSL:

```bash
# 1. Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# 2. Install certbot on host (if not installed)
apt-get update && apt-get install -y certbot

# 3. Get SSL certificate
certbot certonly --standalone -d fsp.tw1.ru

# 4. Copy certificates to project
mkdir -p /opt/fair-sber-price/ssl_copy
cp -r /etc/letsencrypt/* /opt/fair-sber-price/ssl_copy/

# 5. Update docker-compose.prod.yml nginx section:
#    Change: ./nginx.conf.nossl:/etc/nginx/nginx.conf:ro
#    To:     ./nginx.conf:/etc/nginx/nginx.conf:ro
#    Add back: - "443:443"
#    Add back: - ./ssl_copy:/etc/letsencrypt:ro

# 6. Restart nginx
docker-compose -f docker-compose.prod.yml up -d nginx
```

## Verification

After running the fix, verify everything works:

```bash
# Check container status
docker ps

# Check web service
curl http://localhost:8000/api/health/

# Check nginx
curl http://fsp.tw1.ru

# View logs
docker logs fsp_web
docker logs fsp_telegram_bot
docker logs fsp_nginx
```

## Troubleshooting

### If telegram bot still fails:
```bash
# Check database file exists and is readable
ls -la fsp/db/db.sqlite3

# Make it world-readable (temporary fix)
chmod 666 fsp/db/db.sqlite3

# Restart bot
docker-compose -f docker-compose.prod.yml restart telegram-bot
```

### If web service health check fails:
```bash
# Check if database is initialized
docker exec fsp_web python manage.py showmigrations

# Run migrations if needed
docker exec fsp_web python manage.py migrate
```

### If nginx still crashes:
```bash
# Verify config file is correct
docker exec fsp_nginx nginx -t

# Check which config is mounted
docker exec fsp_nginx cat /etc/nginx/nginx.conf | head -20
```
