#!/bin/bash

# Server setup script for DigitalOcean Ubuntu 22.04
# Run this script on your DigitalOcean droplet as root

set -e

echo "🚀 Setting up Fair Sber Price server..."

# Update system
apt-get update && apt-get upgrade -y

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first:"
    echo "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "✅ Docker Compose already installed"
fi

# Ensure Docker is running
systemctl enable docker
systemctl start docker

echo "✅ Docker setup verified"

# Create application directory
mkdir -p /opt/fair-sber-price
cd /opt/fair-sber-price

# Clone repository
git clone https://github.com/grigra27/fair_sber_price.git .

# Create logs directory
mkdir -p fsp/logs
chmod 755 fsp/logs

# Create SSL directory for future use
mkdir -p ssl

# Create environment file template
cat > .env.template << EOF
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
REDIS_URL=redis://redis:6379/0
EOF

echo "📝 Please edit .env file with your actual values:"
echo "cp .env.template .env"
echo "nano .env"

# Set up firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Create systemd service for auto-restart
cat > /etc/systemd/system/fair-sber-price.service << EOF
[Unit]
Description=Fair Sber Price Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/fair-sber-price
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl enable fair-sber-price.service

# Create backup script
cat > /opt/fair-sber-price/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/fair-sber-price"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp fsp/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz fsp/logs/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sqlite3" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/fair-sber-price/backup.sh

# Add backup to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/fair-sber-price/backup.sh") | crontab -

# Create log rotation
cat > /etc/logrotate.d/fair-sber-price << EOF
/opt/fair-sber-price/fsp/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

echo "✅ Server setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file: nano .env"
echo "2. Start the application: systemctl start fair-sber-price"
echo "3. Check status: systemctl status fair-sber-price"
echo "4. View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🔧 Useful commands:"
echo "- Restart: systemctl restart fair-sber-price"
echo "- Update: git pull && docker-compose -f docker-compose.prod.yml up -d --build"
echo "- Backup: ./backup.sh"