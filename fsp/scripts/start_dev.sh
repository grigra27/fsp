#!/bin/bash

# Development startup script for Fair Sber Price
set -e

echo "Starting Fair Sber Price in development mode..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "Virtual environment not found. Please create one with:"
    echo "python -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Check if Django is installed
python -c "import django" 2>/dev/null || {
    echo "Django not found. Installing dependencies..."
    pip install -r requirements.txt
}

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Start the development server
echo "Starting development server..."
python manage.py runserver