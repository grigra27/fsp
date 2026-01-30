#!/bin/bash
# Setup SSL certificates for Fair Sber Price

set -e

DOMAIN="fsp.tw1.ru"
PROJECT_DIR="/opt/fair-sber-price"

echo "=== SSL Certificate Setup for $DOMAIN ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root"
    exit 1
fi

# Stop nginx to free port 80
echo "1. Stopping nginx container..."
cd $PROJECT_DIR
docker-compose -f docker-compose.prod.yml stop nginx

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    echo "2. Installing certbot..."
    apt-get update
    apt-get install -y certbot
else
    echo "2. Certbot already installed"
fi

# Get certificate
echo "3. Obtaining SSL certificate for $DOMAIN..."
certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || {
    echo "Error: Failed to obtain certificate"
    echo "Make sure:"
    echo "  - Port 80 is accessible from the internet"
    echo "  - DNS for $DOMAIN points to this server"
    echo "  - No firewall is blocking port 80"
    exit 1
}

# Copy certificates to project
echo "4. Copying certificates to project directory..."
mkdir -p $PROJECT_DIR/ssl_copy
cp -r /etc/letsencrypt/* $PROJECT_DIR/ssl_copy/
chmod -R 755 $PROJECT_DIR/ssl_copy

# Update docker-compose.yml
echo "5. Updating docker-compose configuration..."
cd $PROJECT_DIR

# Backup current config
cp docker-compose.prod.yml docker-compose.prod.yml.backup

# Update nginx configuration
sed -i 's|./nginx.conf.nossl:/etc/nginx/nginx.conf:ro|./nginx.conf:/etc/nginx/nginx.conf:ro|g' docker-compose.prod.yml
sed -i 's|- "80:80"|- "80:80"\n      - "443:443"|g' docker-compose.prod.yml
sed -i '/- static_files:\/var\/www\/static:ro/a\      - ./ssl_copy:/etc/letsencrypt:ro' docker-compose.prod.yml

echo "6. Starting nginx with SSL..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to start
sleep 5

# Check nginx status
if docker ps | grep -q fsp_nginx; then
    echo ""
    echo "=== SSL Setup Complete ==="
    echo "Your site is now available at:"
    echo "  - https://$DOMAIN"
    echo "  - http://$DOMAIN (redirects to HTTPS)"
    echo ""
    echo "Certificate will expire in 90 days."
    echo "Set up auto-renewal with: certbot renew --dry-run"
else
    echo ""
    echo "=== Error: Nginx failed to start ==="
    echo "Checking logs..."
    docker logs fsp_nginx --tail 50
    echo ""
    echo "Restoring backup configuration..."
    mv docker-compose.prod.yml.backup docker-compose.prod.yml
    docker-compose -f docker-compose.prod.yml up -d nginx
    exit 1
fi
