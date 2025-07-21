#!/bin/bash

# Cron script to save price snapshots
# Add to crontab: 0 */4 * * * /path/to/fsp/scripts/cron_save_snapshot.sh

# Change to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Run the management command
python manage.py save_price_snapshot

# Log the execution
echo "$(date): Price snapshot saved" >> logs/cron.log