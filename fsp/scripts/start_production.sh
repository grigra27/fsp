#!/bin/bash

# Production startup script for Fair Sber Price
set -e

echo "Starting Fair Sber Price in production mode..."

# Set production environment
export DJANGO_SETTINGS_MODULE=fsp.production

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Install production dependencies
echo "Installing production dependencies..."
pip install -r requirements-prod.txt

# Check required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "ERROR: SECRET_KEY environment variable is required"
    exit 1
fi

if [ -z "$ALLOWED_HOSTS" ]; then
    echo "ERROR: ALLOWED_HOSTS environment variable is required"
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
fi

# Clean up old data
echo "Cleaning up old data..."
python manage.py cleanup_old_data --days 90

# Start the application
echo "Starting gunicorn server..."
exec gunicorn fsp.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-3} \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile -